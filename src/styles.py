APP_STYLESHEET = """
/* General Application Styles */
QMainWindow {
    background-color: #f9fafb;
}

QLabel {
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    color: #333;
}

QPushButton {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0078d4, stop: 1 #005bb5);
    border: none;
    color: white;
    padding: 10px;
    border-radius: 8px;
    font-size: 14px;
    text-align: center;
}

QPushButton:hover {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #005bb5, stop: 1 #004085);
}

QPushButton:pressed {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #004085, stop: 1 #002a53);
}

QPushButton:disabled {
    background-color: #a6a6a6;
    color: #ffffff;
}

QTextEdit {
    background-color: #ffffff;
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 10px;
    font-family: 'Consolas', monospace;
    font-size: 14px;
    color: #333;
}

QGroupBox {
    background-color: #ffffff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 10px;
    margin-top: 15px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 10px;
    font-weight: bold;
    color: #0078d4;
}

QRadioButton {
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    color: #333;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 5px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    color: #333;
}

QScrollArea {
    background-color: #ffffff;
    border: none;
}

QMessageBox {
    background-color: #ffffff;
    border: 1px solid #ddd;
    border-radius: 8px;
}

QMessageBox QLabel {
    color: #333;
    font-size: 14px;
}

/* Status Label */
QLabel#status_label {
    font-size: 16px;
    font-weight: bold;
    color: #0078d4;
}

/* Error Status */
QLabel#error_status {
    color: #e74c3c;
}

/* Transcription Text Area */
QTextEdit#transcription_text {
    background-color: #f0f8ff;
    border: 1px solid #b3d4fc;
    border-radius: 8px;
    padding: 10px;
    font-family: 'Consolas', monospace;
    font-size: 14px;
    color: #333;
}

/* Command Group */
QGroupBox#command_group {
    background-color: #ffffff;
    border: 1px solid #b3d4fc;
    border-radius: 8px;
    padding: 10px;
}

QLabel#command_label {
    font-family: 'Consolas', monospace;
    font-size: 14px;
    color: #333;
}

/* Email Group */
QGroupBox#email_group {
    background-color: #ffffff;
    border: 1px solid #b3d4fc;
    border-radius: 8px;
    padding: 10px;
}

QLabel#email_label {
    font-family: 'Consolas', monospace;
    font-size: 14px;
    color: #333;
}

/* Jira Group */
QGroupBox#jira_group {
    background-color: #ffffff;
    border: 1px solid #b3d4fc;
    border-radius: 8px;
    padding: 10px;
}

QLabel#jira_label {
    font-family: 'Consolas', monospace;
    font-size: 14px;
    color: #333;
}

/* Taskcrafters Group */
QGroupBox#taskcrafters_group {
    background-color: #ffffff;
    border: 1px solid #b3d4fc;
    border-radius: 8px;
    padding: 10px;
}

QLabel#taskcrafters_label {
    font-family: 'Consolas', monospace;
    font-size: 14px;
    color: #333;
}

/* Hover Effects for Buttons */
QPushButton#record_button {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ff5722, stop: 1 #d32f2f);
    border: none;
    color: white;
    padding: 15px;
    border-radius: 10px;
    font-size: 16px;
    text-align: center;
}

QPushButton#record_button:hover {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d32f2f, stop: 1 #b71c1c);
}

QPushButton#record_button:pressed {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #b71c1c, stop: 1 #8b0000);
}

/* Shadow Effect for Groups */
QGroupBox {
    box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
}

/* Animation for Buttons */
QPushButton {
    transition: background-color 0.3s ease;
}
"""