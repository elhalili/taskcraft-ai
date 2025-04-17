import sys
import os
import platform
import sounddevice as sd
import numpy as np
import time
import subprocess
from dotenv import load_dotenv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTextEdit, QPushButton, QVBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot
from pywhispercpp.model import Model
import pywhispercpp.constants
from openai import OpenAI


class TranscriptionWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(self, model, audio, platform_name, api_key):
        super().__init__()
        self.model = model
        self.audio = audio
        self.platform_name = platform_name
        self.api_key = api_key

    def run(self):
        try:
            self.status_update.emit("🔊 Transcribing audio...")
            result = self.model.transcribe(self.audio)

            self.status_update.emit("🤖 Sending to Nebius AI...")

            client = OpenAI(
                base_url="https://api.studio.nebius.com/v1/",
                api_key=self.api_key
            )

            prompt = (
                f"I am using {self.platform_name}. Please give me only a Bash or PowerShell command that can accomplish the following task:\n\n"
                f"{result}\n\n"
                "Do not include explanations or comments. Only output the raw command that can be copied and run directly in the terminal."
            )

            completion = client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            command = completion.choices[0].message.content
            final_output = f"{result}\n\nGenerated Command:\n{command}"
            self.finished.emit(final_output)
        except Exception as e:
            self.error.emit(str(e))


class WhisperApp(QWidget):
    gui_status_update = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Whisper Transcriber (Qt)")
        self.resize(600, 400)

        self.model = Model("tiny.en", print_realtime=False)
        self.sample_rate = pywhispercpp.constants.WHISPER_SAMPLE_RATE
        self.channels = 1
        self.recording = False

        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)

        self.record_button = QPushButton("Hold to Record")
        self.record_button.setCheckable(True)

        layout = QVBoxLayout()
        layout.addWidget(self.text_box)
        layout.addWidget(self.record_button)
        self.setLayout(layout)

        self.record_button.pressed.connect(self.start_recording)
        self.record_button.released.connect(self.stop_recording)

        self.gui_status_update.connect(self.update_status_text)

        load_dotenv()
        self.api_key = os.getenv("NEBIUS_API_KEY")
        if not self.api_key:
            QMessageBox.critical(self, "API Key Missing", "No Nebius API key found in .env file.")
            sys.exit(1)

        self.platform_name = self.detect_platform()

    def detect_platform(self):
        system = platform.system()
        if system == "Linux":
            return "Debian Linux"
        elif system == "Windows":
            return "Windows 10"
        else:
            return "a Unix-like OS"

    def start_recording(self):
        self.recording = True
        self.audio_data = []
        self.gui_status_update.emit("🎙️ Recording... Release button to stop.")

        self.record_thread = QThread()
        self.recorder = AudioRecorder(self.sample_rate, self.channels)
        self.recorder.moveToThread(self.record_thread)

        self.record_thread.started.connect(self.recorder.record)
        self.recorder.finished.connect(self.record_thread.quit)
        self.recorder.finished.connect(self.recorder.deleteLater)
        self.record_thread.finished.connect(self.record_thread.deleteLater)

        self.recorder.finished.connect(self.run_transcription_thread)

        self.record_thread.start()

    def stop_recording(self):
        self.recording = False
        if hasattr(self, "recorder"):
            self.recorder.stop()

    def run_transcription_thread(self, audio):
        self.gui_status_update.emit("⏳ Preparing transcription...")

        self.worker_thread = QThread()
        self.worker = TranscriptionWorker(self.model, audio, self.platform_name, self.api_key)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_transcription_done)
        self.worker.error.connect(self.on_transcription_error)
        self.worker.status_update.connect(self.gui_status_update.emit)

        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    @pyqtSlot(str)
    def on_transcription_done(self, text):
        self.text_box.setPlainText(text)

        command = text.split("Generated Command:\n")[-1].strip()
        reply = QMessageBox.question(
            self, "Confirm Action", f"Execute this command?\n\n{command}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            subprocess.Popen(command, shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             text=True)

    @pyqtSlot(str)
    def on_transcription_error(self, message):
        self.text_box.setPlainText(f"❌ Error: {message}")

    @pyqtSlot(str)
    def update_status_text(self, message):
        self.text_box.setPlainText(message)


class AudioRecorder(QObject):
    finished = pyqtSignal(np.ndarray)

    def __init__(self, sample_rate, channels):
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = True

    def stop(self):
        self.recording = False

    def record(self):
        duration = 60
        frames = int(duration * self.sample_rate)
        buffer = np.empty((frames, self.channels), dtype=np.float32)
        idx = 0

        def callback(indata, frames, time_info, status):
            nonlocal idx
            if self.recording and idx + len(indata) < len(buffer):
                buffer[idx:idx+len(indata)] = indata
                idx += len(indata)
            else:
                raise sd.CallbackStop()

        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, callback=callback):
            try:
                while self.recording:
                    time.sleep(0.1)
            except sd.CallbackStop:
                pass

        audio = buffer[:idx]
        self.finished.emit(audio)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhisperApp()
    window.show()
    sys.exit(app.exec_())
