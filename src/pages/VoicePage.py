from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from VoskWorker import VoskWorker
from util import keybindingsJsonPath
import pyautogui as pag
import json

# Maps the string from gui.py to the object required by the 'pynput' library
keybinds_to_pyauto = {
    "Ctrl": "ctrl",
    "Alt": "alt",
    "Shift": "shift",
    "Cmd": "command",   # macOS command key
    "Enter": "enter",
    "Tab": "tab",
    "Backspace": "backspace",
    "Space": "space",
    "Esc": "esc",
    "Up": "up",
    "Down": "down",
    "Left": "left",
    "Right": "right",
    "Delete": "delete",
    "Home": "home",
    "End": "end",
    "PageUp": "pageup",
    "PageDown": "pagedown",
    # function keys (add as needed)
    "F1": "f1", "F2": "f2", "F3": "f3", "F4": "f4", "F5": "f5",
    "F6": "f6", "F7": "f7", "F8": "f8", "F9": "f9", "F10": "f10",
    "F11": "f11", "F12": "f12",
}

# Mouse button mapping (PyAutoGUI only supports left/right/middle)
keybinds_to_mouse_pyauto = {
    "LMB": "left",
    "RMB": "right",
    "MMB": "middle",
}

class VoicePage(QWidget):
    request_start = pyqtSignal()
    request_stop = pyqtSignal()

    def __init__(self, profile_manager):
        super().__init__()
        self.profile_manager = profile_manager
        
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
        self.setLayout(layout)

        # --- Vosk Thread Setup ---
        model_path = "./vosk-model-en-us-0.22-lgraph"  # CHANGE THIS PATH
        self.vosk_thread = QThread()
        self.vosk_worker = VoskWorker(model_path)
        self.vosk_worker.moveToThread(self.vosk_thread)

        # --- Connections ---
        self.vosk_thread.started.connect(self.initialize_worker)
        self.vosk_worker.modelReady.connect(self.on_model_ready)
        self.vosk_worker.textRecognized.connect(self.update_label)
        self.vosk_worker.textRecognized.connect(self.add_text_to_log)
        self.vosk_worker.textRecognized.connect(self.play_key)
        
        self.profile_manager.profileChanged.connect(self.on_profile_changed)

        self.request_start.connect(self.vosk_worker.start_listening)
        self.request_stop.connect(self.vosk_worker.stop_listening)

        self.button.toggled.connect(self.toggle_listening)

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
    def play_key(self, text):
        """Looks up the voice command and simulates the corresponding key/mouse action using pyautogui."""
        data = self.profile_manager.get_keybindings()
        if not data:
            return

        action = data.get(text)  # e.g., "LMB", "Enter", "Ctrl+S", "a"
        if action is None:
            print(f"No key associated with '{text}'")
            return

        print(f"Voice command '{text}' -> action '{action}'")

        # Mouse?
        if action in keybinds_to_mouse_pyauto:
            btn = keybinds_to_mouse_pyauto[action]
            print(f"-> Mouse click: {btn}")
            pag.click(button=btn)
            return

        # Key chord? e.g., "Ctrl+S" or "Cmd+Shift+3"
        if "+" in action:
            parts_raw = [p.strip() for p in action.split("+")]
            parts = []
            for p in parts_raw:
                parts.append(keybinds_to_pyauto.get(p, p.lower()))  # map known names else lowercase
            print(f"-> Hotkey: {parts}")
            pag.hotkey(*parts)
            return

        # Single key (special or character)
        keyname = keybinds_to_pyauto.get(action, action.lower())
        print(f"-> Key press: {keyname}")
        pag.press(keyname)
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
    @pyqtSlot(dict)
    def on_profile_changed(self, profile_data):
        """When the profile changes, re-initialize the worker with new grammar."""
        print("VoicePage detected profile change. Re-initializing grammar.")
        keybindings = profile_data.get("keybindings", {})
        self.vosk_worker.initialize(keybindings)
    @pyqtSlot()
    def initialize_worker(self):
        """Grabs the current keybindings and initializes the worker."""
    
        keybindings = self.profile_manager.get_keybindings()
        
        self.vosk_worker.initialize(keybindings)



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
        self.vosk_worker.stop_listening()
        self.vosk_thread.quit()
        self.vosk_thread.wait()
        event.accept()