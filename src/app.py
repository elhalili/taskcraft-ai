import json
import sys
import os
import sounddevice as sd
import numpy as np
import threading
import queue
from pywhispercpp.model import Model

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QMessageBox, QGroupBox, QSizePolicy,
    QRadioButton, QDialog, QLineEdit, QFormLayout, QTabWidget, QScrollArea, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QSettings
from PyQt6.QtGui import QFont, QPalette, QColor

SAMPLE_RATE = 16000
CHANNELS = 1

class WorkerSignals(QObject):
    result = pyqtSignal(str, object)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setModal(True)
        self.settings = QSettings("VoiceCommandApp", "VoiceRecorder")

        self.contacts_group = QGroupBox("Contacts Management")
        
        self.contacts_path_label = QLabel("No contacts file loaded")
        self.load_contacts_button = QPushButton("Load Contacts File")
        self.load_contacts_button.clicked.connect(self.load_contacts_file)
        
        
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QFormLayout(scroll_content)
        
        self.nebius_group = QGroupBox("Nebius API Settings")
        nebius_layout = QFormLayout(self.nebius_group)
        
        self.nebius_api_key_input = QLineEdit()
        self.nebius_base_url_input = QLineEdit()
        self.nebius_model_input = QLineEdit()
        
        nebius_layout.addRow("Nebius API Key:", self.nebius_api_key_input)
        nebius_layout.addRow("Nebius Base URL:", self.nebius_base_url_input)
        nebius_layout.addRow("Nebius Model:", self.nebius_model_input)

        
        scroll_layout.addRow(self.nebius_group)
        
        self.email_settings_group = QGroupBox("Email Settings")
        email_settings_layout = QFormLayout(self.email_settings_group)
        
        self.sender_email_input = QLineEdit()
        self.sender_password_input = QLineEdit()
        self.sender_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.default_recipient_input = QLineEdit()
        
        email_settings_layout.addRow("Sender Email:", self.sender_email_input)
        email_settings_layout.addRow("App Password:", self.sender_password_input)
        email_settings_layout.addRow("Default Recipient:", self.default_recipient_input)
        
        scroll_layout.addRow(self.email_settings_group)
        
        self.whisper_settings_group = QGroupBox("Whisper Settings")
        whisper_settings_layout = QFormLayout(self.whisper_settings_group)
        
        self.whisper_model_input = QLineEdit()
        self.whisper_lang_input = QLineEdit()
        self.whisper_threads_input = QLineEdit()
        
        whisper_settings_layout.addRow("Model Name:", self.whisper_model_input)
        whisper_settings_layout.addRow("Language:", self.whisper_lang_input)
        whisper_settings_layout.addRow("Thread Count:", self.whisper_threads_input)

        contacts_layout = QVBoxLayout(self.contacts_group)
        contacts_layout.addWidget(self.contacts_path_label)
        contacts_layout.addWidget(self.load_contacts_button)
        scroll_layout.addRow(self.contacts_group)

        
        scroll_layout.addRow(self.whisper_settings_group)
        
        scroll.setWidget(scroll_content)
        general_layout.addWidget(scroll)
        
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        general_layout.addLayout(button_layout)
        
        tab_widget.addTab(general_tab, "General Settings")
        self.setMinimumSize(600, 500)

    def load_contacts_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Contacts JSON File", 
            "", 
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            try:
                # Validate the contacts file
                with open(file_path, 'r') as f:
                    contacts = json.load(f)
                    if not isinstance(contacts, dict):
                        raise ValueError("Contacts file should contain a dictionary")
                
                # Save the contacts path to settings
                self.settings.setValue("contacts/path", file_path)
                self.contacts_path_label.setText(f"Loaded: {os.path.basename(file_path)}")
                QMessageBox.information(self, "Success", "Contacts file loaded successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Invalid contacts file: {str(e)}")


    def load_settings(self):
        self.nebius_api_key_input.setText(self.settings.value("nebius/api_key", ""))
        self.nebius_base_url_input.setText(self.settings.value("nebius/base_url", ""))
        self.nebius_model_input.setText(self.settings.value("nebius/model", ""))
        self.sender_email_input.setText(self.settings.value("email/sender", ""))
        self.sender_password_input.setText(self.settings.value("email/password", ""))
        self.default_recipient_input.setText(self.settings.value("email/default_recipient", ""))
        self.whisper_model_input.setText(self.settings.value("whisper/model", "base"))
        self.whisper_lang_input.setText(self.settings.value("whisper/lang", "en"))
        self.whisper_threads_input.setText(self.settings.value("whisper/threads", "4"))
        contacts_path = self.settings.value("contacts/path", "")
        if contacts_path:
            self.contacts_path_label.setText(f"Loaded: {os.path.basename(contacts_path)}")

    def save_settings(self):
        self.settings.setValue("nebius/api_key", self.nebius_api_key_input.text())
        self.settings.setValue("nebius/base_url", self.nebius_base_url_input.text())
        self.settings.setValue("nebius/model", self.nebius_model_input.text())
        self.settings.setValue("email/sender", self.sender_email_input.text())
        self.settings.setValue("email/password", self.sender_password_input.text())
        self.settings.setValue("email/default_recipient", self.default_recipient_input.text())
        self.settings.setValue("whisper/model", self.whisper_model_input.text())
        self.settings.setValue("whisper/lang", self.whisper_lang_input.text())
        self.settings.setValue("whisper/threads", self.whisper_threads_input.text())
        self.accept()

    def get_settings(self):
        return {
            "nebius": {
                "api_key": self.settings.value("nebius/api_key", ""),
                "base_url": self.settings.value("nebius/base_url", ""),
                "model": self.settings.value("nebius/model", "")
            },
            "email": {
                "sender": self.settings.value("email/sender", ""),
                "password": self.settings.value("email/password", ""),
                "default_recipient": self.settings.value("email/default_recipient", "")
            },
            "contacts": {
                "path": self.settings.value("contacts/path", "")
            },
            "whisper": {
                "model": self.settings.value("whisper/model", "base"),
                "lang": self.settings.value("whisper/lang", "en"),
                "threads": int(self.settings.value("whisper/threads", 4))
            }
        }

class VoiceRecorderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Whisper Voice Recorder (Qt)")
        
        # Initialize variables
        self.is_recording = False
        self.audio_data = []
        self.stream = None
        self.current_transcription = ""
        self.suggested_command = ""
        self.result_queue = queue.Queue()
        self.current_mode = "command"
        
        # Initialize UI first
        self.init_ui()
        
        # Then initialize other components
        self.settings_dialog = SettingsDialog(self)
        self.app_settings = self.settings_dialog.get_settings()
        self.update_environment_variables()
        
        # Initialize whisper model
        self.model = Model(
            self.app_settings["whisper"]["model"],
            language=self.app_settings["whisper"]["lang"],
            n_threads=self.app_settings["whisper"]["threads"],
            print_realtime=False
        )
        
        # Now safe to call methods that use UI elements
        self.check_audio_input()
        self.set_ui_state('idle')
        
        # Set up queue timer
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.check_queue)
        self.queue_timer.start(100)

        self.contacts = {}
        self.load_contacts()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Menu Bar
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        settings_action = settings_menu.addAction("Open Settings")
        settings_action.triggered.connect(self.open_settings)

        # Mode Selection
        mode_group = QGroupBox("Mode Selection")
        mode_layout = QHBoxLayout(mode_group)
        
        self.command_radio = QRadioButton("Command Mode")
        self.command_radio.setChecked(True)
        self.command_radio.toggled.connect(lambda: self.set_mode("command"))
        
        self.email_radio = QRadioButton("Email Mode")
        self.email_radio.toggled.connect(lambda: self.set_mode("email"))
        
        mode_layout.addWidget(self.command_radio)
        mode_layout.addWidget(self.email_radio)
        main_layout.addWidget(mode_group)

        # Status Label
        self.status_label = QLabel("Status: Idle. Press Record.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(self.status_label)

        # Record Button
        self.record_button = QPushButton("Record")
        self.record_button.setMinimumHeight(40)
        self.record_button.clicked.connect(self.toggle_recording)
        main_layout.addWidget(self.record_button)

        # Transcription Group
        transcription_group = QGroupBox("Transcription / Instruction")
        transcription_layout = QVBoxLayout(transcription_group)
        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setMinimumHeight(80)
        transcription_layout.addWidget(self.transcription_text)
        main_layout.addWidget(transcription_group)

        # Command Group
        self.command_group = QGroupBox("Suggested Command")
        command_layout = QVBoxLayout(self.command_group)
        self.command_label = QLabel("...")
        self.command_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.command_label.setFont(QFont("Consolas", 10))
        self.command_label.setWordWrap(True)
        command_layout.addWidget(self.command_label)

        button_layout = QHBoxLayout()
        self.execute_button = QPushButton("Execute Command")
        self.execute_button.clicked.connect(self.execute_suggested_command)
        self.execute_button.setEnabled(False)
        button_layout.addWidget(self.execute_button)

        self.cancel_button = QPushButton("Clear/Cancel")
        self.cancel_button.clicked.connect(self.clear_command)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)

        command_layout.addLayout(button_layout)
        main_layout.addWidget(self.command_group)

        # Email Group
        self.email_group = QGroupBox("Email Content")
        email_layout = QVBoxLayout(self.email_group)
        self.email_label = QLabel("...")
        self.email_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.email_label.setFont(QFont("Consolas", 10))
        self.email_label.setWordWrap(True)
        email_layout.addWidget(self.email_label)
        
        email_button_layout = QHBoxLayout()
        self.send_email_button = QPushButton("Send Email")
        self.send_email_button.clicked.connect(self.send_email_command)
        self.send_email_button.setEnabled(False)
        email_button_layout.addWidget(self.send_email_button)
        
        self.cancel_email_button = QPushButton("Clear/Cancel")
        self.cancel_email_button.clicked.connect(self.clear_command)
        self.cancel_email_button.setEnabled(False)
        email_button_layout.addWidget(self.cancel_email_button)
        
        email_layout.addLayout(email_button_layout)
        main_layout.addWidget(self.email_group)
        self.email_group.hide()

    def load_contacts(self):
        """Load contacts from the configured JSON file"""
        contacts_path = self.app_settings["contacts"]["path"]
        if contacts_path and os.path.exists(contacts_path):
            try:
                with open(contacts_path, 'r') as f:
                    self.contacts = json.load(f)
                    if not isinstance(self.contacts, dict):
                        raise ValueError("Contacts file should contain a dictionary")
                print(f"Loaded {len(self.contacts)} contacts")
            except Exception as e:
                print(f"Error loading contacts: {e}")
                self.contacts = {}

    def set_ui_state(self, state):
        if state == 'idle':
            self.record_button.setText("Record")
            self.record_button.setEnabled(True)
            self.execute_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.send_email_button.setEnabled(False)
            self.cancel_email_button.setEnabled(False)
            self.update_status("Idle. Press Record.")
        elif state == 'recording':
            self.record_button.setText("Stop Recording")
            self.record_button.setEnabled(True)
            self.execute_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.send_email_button.setEnabled(False)
            self.cancel_email_button.setEnabled(False)
            self.update_transcription_display("Recording...")
            self.update_command_display("...")
            self.update_email_display("...")
            self.update_status("Recording audio...")
        elif state == 'processing':
            self.record_button.setText("Processing...")
            self.record_button.setEnabled(False)
            self.execute_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.send_email_button.setEnabled(False)
            self.cancel_email_button.setEnabled(False)
        elif state == 'awaiting_confirmation':
            self.record_button.setText("Record")
            self.record_button.setEnabled(True)
            if self.current_mode == "command":
                self.execute_button.setEnabled(True)
                self.cancel_button.setEnabled(True)
            else:
                self.send_email_button.setEnabled(True)
                self.cancel_email_button.setEnabled(True)
            self.update_status("Review suggested command and Execute or Clear.")

    def check_audio_input(self):
        try:
            sd.check_input_settings(samplerate=SAMPLE_RATE, channels=CHANNELS)
        except Exception as e:
            error_msg = f"Could not open microphone. Make sure one is connected and permissions are granted.\nError: {e}"
            self.update_status("Audio Error: Could not open microphone!", is_error=True)
            QMessageBox.critical(self, "Audio Error", error_msg)
            self.record_button.setEnabled(False)

    def update_environment_variables(self):
        os.environ["NEBIUS_API_KEY"] = self.app_settings["nebius"]["api_key"]
        os.environ["NEBIUS_BASE_URL"] = self.app_settings["nebius"]["base_url"]
        os.environ["MODEL"] = self.app_settings["nebius"]["model"]
        os.environ["GMAIL_USER"] = self.app_settings["email"]["sender"]
        os.environ["GMAIL_APP_PASSWORD"] = self.app_settings["email"]["password"]

    def open_settings(self):
        if self.settings_dialog.exec() == QDialog.DialogCode.Accepted:
            self.app_settings = self.settings_dialog.get_settings()
            self.update_environment_variables()
            self.model = Model(
                self.app_settings["whisper"]["model"],
                language=self.app_settings["whisper"]["lang"],
                n_threads=self.app_settings["whisper"]["threads"],
                print_realtime=False
            )
            self.update_status("Settings updated successfully")

    def set_mode(self, mode):
        self.current_mode = mode
        if mode == "command":
            self.command_group.show()
            self.email_group.hide()
        else:
            self.command_group.hide()
            self.email_group.show()
        self.clear_command()

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

    def update_email_display(self, text):
        self.email_label.setText(text if text else "...")

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
            audio_float32 = (recording / 32768.0).astype(np.float32)

            self.update_status("Transcribing audio (Whisper)...")
            self.update_transcription_display("Transcribing...")

            transcribe_thread = threading.Thread(target=self.run_whisper, args=(audio_float32,))
            transcribe_thread.daemon = True
            transcribe_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Processing Error", f"Error processing audio: {e}")
            self.update_status("Status: Error processing audio", is_error=True)
            self.set_ui_state('idle')

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def run_whisper(self, audio_data):
        try:
            segments = self.model.transcribe(audio_data)
            transcription = " ".join(segment.text for segment in segments)
            print(f"Whisper Output:\n{transcription}")
            self.result_queue.put(("transcription_success", transcription))
        except Exception as e:
            error_message = f"An unexpected error occurred during transcription: {e}"
            print(error_message, flush=True)
            self.result_queue.put(("transcription_error", error_message))

    def run_gpt_command_thread(self, instruction):
        try:
            if self.current_mode == "command":
                command, error = get_cmd(instruction)
                if error:
                    self.result_queue.put(("gpt_error", error))
                elif command:
                    self.result_queue.put(("gpt_success", command))
                else:
                    self.result_queue.put(("gpt_error", "Failed to generate command (Unknown reason)."))
            else:
                email_data = generate_email_from_prompt(instruction, self.contacts)
                if email_data:
                    self.result_queue.put(("email_success", email_data))
                else:
                    self.result_queue.put(("email_error", "Failed to generate email content."))
        except Exception as e:
            error_message = f"An unexpected error occurred during command generation: {e}"
            print(error_message, flush=True)
            if self.current_mode == "command":
                self.result_queue.put(("gpt_error", error_message))
            else:
                self.result_queue.put(("email_error", error_message))

    def check_queue(self):
        try:
            message_type, data = self.result_queue.get_nowait()

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
                QMessageBox.critical(self, "Transcription Error", data)
                self.set_ui_state('idle')

            elif message_type == "gpt_success":
                self.suggested_command = data
                self.update_command_display(self.suggested_command)
                self.set_ui_state('awaiting_confirmation')

            elif message_type == "gpt_error":
                self.update_command_display(f"Error generating command.")
                self.update_status(f"Command generation failed", is_error=True)
                QMessageBox.critical(self, "Command Generation Error", data)
                self.set_ui_state('idle')
                
            elif message_type == "email_success":
                self.suggested_command = data
                email_text = f"To: {data['contact']}\nSubject: {data['subject']}\n\n{data['body']}"
                self.update_email_display(email_text)
                self.set_ui_state('awaiting_confirmation')
                
            elif message_type == "email_error":
                self.update_email_display(f"Error generating email content.")
                self.update_status(f"Email generation failed", is_error=True)
                QMessageBox.critical(self, "Email Generation Error", data)
                self.set_ui_state('idle')

        except queue.Empty:
            pass
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
                QTimer.singleShot(2000, lambda: self.set_ui_state('idle'))
            else:
                self.update_status(f"Execution failed", is_error=True)
                QMessageBox.critical(self, "Execution Failed", error_msg)
                self.set_ui_state('awaiting_confirmation')
        else:
            self.update_status("Execution cancelled by user.")
            self.set_ui_state('awaiting_confirmation')

    def send_email_command(self):
        if not self.suggested_command or not isinstance(self.suggested_command, dict):
            return
            
        email_settings = self.app_settings["email"]
        
        if not email_settings["sender"] or not email_settings["password"]:
            QMessageBox.critical(self, "Email Error", "Email settings are not configured. Please set up your email in Settings.")
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Email",
            f"<b>You are about to send the following email:</b><br/><br/>"
            f"<b>To:</b> {self.suggested_command['contact']}<br/>"
            f"<b>Subject:</b> {self.suggested_command['subject']}<br/><br/>"
            f"<b>Body:</b><br/>{self.suggested_command['body']}<br/><br/>"
            "<b>Are you sure you want to send this email?</b>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                send_email(
                    self.suggested_command['contact'],
                    self.suggested_command['subject'],
                    self.suggested_command['body'],
                    sender_email=email_settings["sender"],
                    sender_password=email_settings["password"]
                )
                self.update_status("Email sent successfully!")
                QTimer.singleShot(2000, lambda: self.set_ui_state('idle'))
            except Exception as e:
                self.update_status(f"Failed to send email: {str(e)}", is_error=True)
                QMessageBox.critical(self, "Email Error", f"Failed to send email: {str(e)}")
                self.set_ui_state('awaiting_confirmation')
        else:
            self.update_status("Email cancelled by user.")
            self.set_ui_state('awaiting_confirmation')

    def clear_command(self):
        self.suggested_command = ""
        self.update_command_display("")
        self.update_email_display("")
        self.set_ui_state('idle')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = VoiceRecorderApp()
    # make sure env var are loaded
    from cli_commands import execute_cmd, get_cmd 
    from email_sender import generate_email_from_prompt, send_email

    main_window.show()
    sys.exit(app.exec())