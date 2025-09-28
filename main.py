import sys
import json
import sounddevice as sd
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QTextEdit
from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from vosk import Model, KaldiRecognizer
from src.VoskWorker import VoskWorker




# --- Main Application Window ---
class MainWindow(QMainWindow):
    # Signals to communicate with the worker thread
    request_start = pyqtSignal()
    request_stop = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vosk Speech Recognition (Efficient)")
        self.setGeometry(100, 100, 400, 200)

        self.label = QLabel("Model is loading or not yet started...", self)
        self.button = QPushButton("Start Listening", self)
        self.button.setCheckable(True)
        self.button.setEnabled(False) # Disable button until model is loaded
        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True)
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.log_box)
        layout.addWidget(self.button)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # --- Vosk Thread Setup ---
        model_path = "./vosk-model-small-en-us-0.15"  # CHANGE THIS PATH
        self.vosk_thread = QThread()
        self.vosk_worker = VoskWorker(model_path)
        self.vosk_worker.moveToThread(self.vosk_thread)
        
        

        # --- Connections ---
        # 1. Initialize the worker when the thread starts
        self.vosk_thread.started.connect(self.vosk_worker.initialize)
        
        self.vosk_worker.textRecognized.connect(self.update_label)
        self.vosk_worker.textRecognized.connect(self.add_text_to_log)

        # 2. Connect signals from main thread to worker's slots
        self.request_start.connect(self.vosk_worker.start_listening)
        self.request_stop.connect(self.vosk_worker.stop_listening)

        # 3. Connect signal from worker to update GUI
        self.vosk_worker.textRecognized.connect(self.update_label)

        # 4. Connect the button toggle to our handler
        self.button.toggled.connect(self.toggle_listening)
        
        self.vosk_worker.modelReady.connect(self.on_model_ready)
        
        # Start the thread. It will now run for the lifetime of the app.
        self.vosk_thread.start()

    @pyqtSlot(str)
    def update_label(self, text):
        if "Error" in text:
            self.label.setText(text)
        elif self.button.isChecked():
            # Only update if we are in a listening state
            current_text = self.label.text()
            if current_text.startswith("Listening..."):
                 self.label.setText(text.capitalize())
            else:
                 self.label.setText(f"{current_text} {text}")
        
        # Once the model is loaded, enable the button
        if "Model loaded successfully" in text or "Error" not in text and not self.button.isEnabled():
            self.button.setEnabled(True)
            self.label.setText("Press 'Start Listening' to begin.")
    @pyqtSlot(str)
    def add_text_to_log(self, text):
        """Appends recognized text to the log box."""
        if "Error" not in text and text: # Don't log errors or empty strings
            self.log_box.append(text) # .append() adds text on a new line
    @pyqtSlot(bool, str)
    def on_model_ready(self, success, message):
        print(message) # Log to console
        if success:
            self.button.setEnabled(True)
            self.label.setText("Press 'Start Listening' to begin.")
        else:
            self.label.setText(message) # Show the error in the GUI
            self.button.setEnabled(False)



    def toggle_listening(self, checked):
        if checked:
            self.label.setText("Listening...")
            self.button.setText("Stop Listening")
            self.request_start.emit() # Emit signal to start
        else:
            self.label.setText("Stopped. Press 'Start Listening' to begin.")
            self.button.setText("Start Listening")
            self.request_stop.emit() # Emit signal to stop

    def closeEvent(self, event):
        """Ensure the thread is stopped cleanly."""
        self.vosk_thread.quit()
        self.vosk_thread.wait()
        event.accept()

# --- Run the Application ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())