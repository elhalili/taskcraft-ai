import sys
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
import threading
import subprocess
import os
import tempfile
import queue


# PyQt6 Imports ---
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QMessageBox, QGroupBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QPalette, QColor

from automation import execute_cmd, get_cmd 

WHISPER_CPP_PATH = r"C:\Users\mucef\Desktop\opportunAI\whisper.cpp"
WHISPER_CPP_EXECUTABLE = os.path.join(WHISPER_CPP_PATH, "build", "bin", "Release", "whisper-cli.exe")
WHISPER_MODEL_PATH = os.path.join(WHISPER_CPP_PATH, "models", "ggml-base.bin")

SAMPLE_RATE = 16000
CHANNELS = 1

class WorkerSignals(QObject):
    result = pyqtSignal(str, object) 

class VoiceRecorderApp(QMainWindow): 
    def __init__(self):
        super().__init__() 
        self.setWindowTitle("Whisper Voice Recorder (Qt)") 

        self.is_recording = False
        self.audio_data = []
        self.stream = None
        self.temp_wav_file = None
        self.current_transcription = ""
        self.suggested_command = ""
        self.result_queue = queue.Queue() # Keep using queue for simplicity as requested

        # --- Central Widget and Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Status Label ---
        self.status_label = QLabel("Status: Idle. Press Record.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # self.status_label.setWordWrap(True) # Optional: Allow wrapping
        main_layout.addWidget(self.status_label)

        # --- Record Button ---
        self.record_button = QPushButton("Record")
        self.record_button.setMinimumHeight(40) # Make button taller
        self.record_button.clicked.connect(self.toggle_recording) # Use clicked.connect
        main_layout.addWidget(self.record_button)

        # --- Transcription GroupBox ---
        transcription_group = QGroupBox("Transcription / Instruction")
        transcription_layout = QVBoxLayout(transcription_group)
        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True) # Equivalent to state=DISABLED
        self.transcription_text.setMinimumHeight(80) # Set a reasonable minimum height
        # self.transcription_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Allow expansion
        transcription_layout.addWidget(self.transcription_text)
        main_layout.addWidget(transcription_group)


        # --- Command GroupBox ---
        command_group = QGroupBox("Suggested Command")
        command_layout = QVBoxLayout(command_group)

        # --- Command Label ---
        self.command_label = QLabel("...")
        self.command_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.command_label.setFont(QFont("Consolas", 10)) # Set monospaced font
        self.command_label.setWordWrap(True) # Allow command to wrap if long
        command_layout.addWidget(self.command_label)

        # --- Button Frame (using QHBoxLayout) ---
        button_layout = QHBoxLayout() # Horizontal layout for buttons

        self.execute_button = QPushButton("Execute Command")
        self.execute_button.clicked.connect(self.execute_suggested_command)
        self.execute_button.setEnabled(False) # Equivalent to state=DISABLED
        button_layout.addWidget(self.execute_button)

        self.cancel_button = QPushButton("Clear/Cancel")
        self.cancel_button.clicked.connect(self.clear_command)
        self.cancel_button.setEnabled(False) # Equivalent to state=DISABLED
        button_layout.addWidget(self.cancel_button)

        # Add button layout to the command group layout
        command_layout.addLayout(button_layout)
        main_layout.addWidget(command_group)

        # --- Initial Checks ---
        checks_ok = True
        if not os.path.exists(WHISPER_CPP_EXECUTABLE):
            error_msg = f"Whisper executable not found at:\n{WHISPER_CPP_EXECUTABLE}\nPlease check the path in the script."
            self.update_status("Error: Whisper executable not found!", is_error=True)
            QMessageBox.critical(self, "Error", error_msg) # Use QMessageBox
            self.record_button.setEnabled(False)
            checks_ok = False
        elif not os.path.exists(WHISPER_MODEL_PATH):
             error_msg = f"Whisper model not found at:\n{WHISPER_MODEL_PATH}\nPlease check the path in the script."
             self.update_status("Error: Whisper model not found!", is_error=True)
             QMessageBox.critical(self, "Error", error_msg) # Use QMessageBox
             self.record_button.setEnabled(False)
             checks_ok = False

        if checks_ok: # Only check audio if paths are okay
            try:
                sd.check_input_settings(samplerate=SAMPLE_RATE, channels=CHANNELS)
            except Exception as e:
                 error_msg = f"Could not open microphone. Make sure one is connected and permissions are granted.\nError: {e}"
                 self.update_status("Audio Error: Could not open microphone!", is_error=True)
                 QMessageBox.critical(self, "Audio Error", error_msg) # Use QMessageBox
                 self.record_button.setEnabled(False)

        # --- Timer for checking the queue ---
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.check_queue)
        self.queue_timer.start(100) 

        self.set_ui_state('idle') 

    def update_status(self, message, is_error=False):
        self.status_label.setText(f"Status: {message}")
        palette = self.status_label.palette()
        if is_error:
             palette.setColor(QPalette.ColorRole.WindowText, QColor("red"))
        else:
             palette.setColor(QPalette.ColorRole.WindowText, QApplication.palette().color(QPalette.ColorRole.WindowText))
        self.status_label.setPalette(palette)

    def update_transcription_display(self, text):
        self.transcription_text.setPlainText(text) 

    def update_command_display(self, text):
        self.command_label.setText(text if text else "...")

    def set_ui_state(self, state):
        if state == 'idle':
            self.record_button.setText("Record")
            self.record_button.setEnabled(True)
            self.execute_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.update_status("Idle. Press Record.")
        elif state == 'recording':
            self.record_button.setText("Stop Recording")
            self.record_button.setEnabled(True)
            self.execute_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.update_transcription_display("Recording...") 
            self.update_command_display("...") 
            self.update_status("Recording audio...")
        elif state == 'processing':
            self.record_button.setText("Processing...")
            self.record_button.setEnabled(False)
            self.execute_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
        elif state == 'awaiting_confirmation':
            self.record_button.setText("Record")
            self.record_button.setEnabled(True) 
            self.execute_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            self.update_status("Review suggested command and Execute or Clear.")


    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Audio Status Warning: {status}", flush=True)
        self.audio_data.append(indata.copy())

    def start_recording(self):
        if self.is_recording:
            return

        self.is_recording = True
        self.audio_data = []
        self.current_transcription = ""
        self.suggested_command = ""
        self.set_ui_state('recording')
        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                callback=self._audio_callback,
                dtype='int16'
            )
            self.stream.start()
        except Exception as e:
            QMessageBox.critical(self, "Recording Error", f"Could not start recording stream: {e}") 
            self.is_recording = False
            self.update_status("Status: Error starting recording", is_error=True)
            self.set_ui_state('idle') 


    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False 
        self.set_ui_state('processing') 
        self.update_status("Stopping recording...") 

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None


            if not self.audio_data:
                self.update_status("Status: No audio recorded.")
                self.set_ui_state('idle') 
                return

            self.update_status("Status: Processing audio...") 

            recording = np.concatenate(self.audio_data, axis=0)

            self.temp_wav_file = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    self.temp_wav_file = f.name
                wav.write(self.temp_wav_file, SAMPLE_RATE, recording)
                print(f"Audio saved temporarily to: {self.temp_wav_file}")

                self.update_status("Transcribing audio (Whisper)...")
                self.update_transcription_display("Transcribing...") 

                transcribe_thread = threading.Thread(target=self.run_whisper, args=(self.temp_wav_file,))
                transcribe_thread.daemon = True
                transcribe_thread.start()
            except Exception as e:
                QMessageBox.critical(self, "Processing Error", f"Error preparing audio for transcription: {e}")
                self.update_status("Status: Error during processing", is_error=True)
                self.set_ui_state('idle')
                self.cleanup_temp_file() 

        except Exception as e:
            QMessageBox.critical(self, "Processing Error", f"Error stopping recording stream: {e}")
            self.update_status("Status: Error stopping recording", is_error=True)
            self.set_ui_state('idle')
            self.cleanup_temp_file() 

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def run_whisper(self, audio_file_path):
        temp_file_to_clean = audio_file_path 
        try:
            command = [
                WHISPER_CPP_EXECUTABLE,
                
                "-f", audio_file_path,
                "-m", WHISPER_MODEL_PATH,
                "-nt", # No timestamps needed for command generation usually
                "-t", "8", # Example: Use 8 threads
            ]
            print(f"Running command: {' '.join(command)}")

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True, # Raise exception on non-zero exit code
                encoding='utf-8', # Ensure correct decoding
                startupinfo=startupinfo # Hide console window
            )

            transcription = process.stdout.strip()
            print(f"Whisper Output:\n{transcription}")
            # Put tuple in queue - GUI thread will handle UI update
            self.result_queue.put(("transcription_success", transcription))

        except FileNotFoundError:
             error_msg = f"Error: Whisper executable not found at {WHISPER_CPP_EXECUTABLE}"
             print(error_msg, flush=True)
             self.result_queue.put(("transcription_error", error_msg))
        except subprocess.CalledProcessError as e:
            error_message = f"Whisper.cpp failed (exit code {e.returncode}):\n{e.stderr}"
            print(error_message, flush=True)
            self.result_queue.put(("transcription_error", error_message))
        except Exception as e:
            error_message = f"An unexpected error occurred during transcription: {e}"
            print(error_message, flush=True)
            self.result_queue.put(("transcription_error", error_message))
        finally:
            # Signal the main thread to clean up the specific temp file
            # Pass the path to ensure the correct file is deleted
            self.result_queue.put(("cleanup_request", temp_file_to_clean))


    def run_gpt_command_thread(self, instruction):
        # This function remains unchanged (interacts via queue)
        try:
            command, error = get_cmd(instruction) 
            if error:
                self.result_queue.put(("gpt_error", error))
            elif command:
                self.result_queue.put(("gpt_success", command))
            else:
                 self.result_queue.put(("gpt_error", "Failed to generate command (Unknown reason)."))
        except Exception as e:
            error_message = f"An unexpected error occurred during command generation: {e}"
            print(error_message, flush=True)
            self.result_queue.put(("gpt_error", error_message))


    def check_queue(self):
        try:
            message_type, data = self.result_queue.get_nowait()

            print(f"Queue received: {message_type}") 

            if message_type == "transcription_success":
                self.current_transcription = data
                self.update_transcription_display(self.current_transcription)
                if self.current_transcription:
                    self.update_status("Generating command (Automation)...")
                    gpt_thread = threading.Thread(target=self.run_gpt_command_thread, args=(self.current_transcription,))
                    gpt_thread.daemon = True
                    gpt_thread.start()
                else:
                    self.update_status("Transcription was empty.", is_error=True)
                    self.set_ui_state('idle')

            elif message_type == "transcription_error":
                self.update_transcription_display(f"Error: {data}")
                self.update_status(f"Transcription failed", is_error=True)
                QMessageBox.critical(self, "Transcription Error", data) # Use QMessageBox
                self.set_ui_state('idle')

            elif message_type == "gpt_success":
                self.suggested_command = data
                self.update_command_display(self.suggested_command)
                self.set_ui_state('awaiting_confirmation') # Set state

            elif message_type == "gpt_error":
                self.update_command_display(f"Error generating command.") 
                self.update_status(f"Command generation failed", is_error=True)
                QMessageBox.critical(self, "Command Generation Error", data)
                self.set_ui_state('idle') 

            elif message_type == "cleanup_request":
                 self.cleanup_temp_file(data) #

        except queue.Empty:
            pass #
        except Exception as e:
             print(f"Error processing queue: {e}", flush=True)
             self.update_status(f"Internal GUI error: {e}", is_error=True)


    def execute_suggested_command(self):
        if not self.suggested_command:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Execution",
            f"<b>WARNING:</b> You are about to execute the following command:<br/><br/>"
            f"<pre>{self.suggested_command}</pre><br/>" 
            "Executing AI-generated commands can be dangerous.<br/><b>Are you sure?</b>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No 
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.update_status(f"Executing: {self.suggested_command}")
            success, error_msg = execute_cmd(self.suggested_command)
            if success:
                 self.update_status("Command sent to new terminal. Resetting.")
                 QTimer.singleShot(2000, lambda: self.set_ui_state('idle')) # Reset after 2s
            else:
                 self.update_status(f"Execution failed", is_error=True)
                 QMessageBox.critical(self, "Execution Failed", error_msg) # Use QMessageBox
                 self.set_ui_state('awaiting_confirmation') # Stay in confirmation state on failure
        else:
            self.update_status("Execution cancelled by user.")
            self.set_ui_state('awaiting_confirmation') # Remain in this state


    def clear_command(self):
        self.suggested_command = ""
        self.update_command_display("...")
      
        self.set_ui_state('idle') 

    def cleanup_temp_file(self, file_path=None):
        path_to_delete = file_path if file_path else self.temp_wav_file

        if path_to_delete and os.path.exists(path_to_delete):
            try:
                os.remove(path_to_delete)
                print(f"Temporary file deleted: {path_to_delete}")
                if path_to_delete == self.temp_wav_file:
                    self.temp_wav_file = None
            except OSError as e:
                print(f"Error deleting temporary file {path_to_delete}: {e}", flush=True)
                
    def closeEvent(self, event):
        
        print("Close event triggered")
        if self.is_recording:
            QMessageBox.warning(self, "Recording Active", "Please stop the recording before closing.")
            event.ignore() 
            return

        self.queue_timer.stop()
        print("Queue timer stopped.")

        if self.stream:
            try:
                if self.stream.active:
                    self.stream.stop()
                self.stream.close()
                print("Audio stream closed.")
            except Exception as e:
                print(f"Error closing stream on exit: {e}", flush=True) # Log error
        self.stream = None

        self.cleanup_temp_file()
        print("Cleanup attempted.")

        event.accept() 

if __name__ == "__main__":
    if not os.path.isdir(os.path.dirname(WHISPER_CPP_EXECUTABLE)):
         print(f"WARNING: Directory for executable does not exist: {os.path.dirname(WHISPER_CPP_EXECUTABLE)}")
    if not os.path.isdir(os.path.dirname(WHISPER_MODEL_PATH)):
         print(f"WARNING: Directory for model does not exist: {os.path.dirname(WHISPER_MODEL_PATH)}")

    # --- PyQt Application Setup ---
    app = QApplication(sys.argv)
    main_window = VoiceRecorderApp()
    main_window.show()
    sys.exit(app.exec())
    # --- End PyQt Application Setup ---