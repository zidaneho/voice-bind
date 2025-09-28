import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
import json

keybindingsJsonPath = "../keybindings.json"

class KeybindMenu(QWidget):
    def __init__(self, key_bindings):
        super().__init__()
        self.key_bindings = key_bindings
        self.setWindowTitle("Keybind Menu")
        self.setLayout(QVBoxLayout())

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Command", "Binding"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout().addWidget(self.table)

        self.refresh_table()

        # --- UI Setup for Input ---
        add_key_layout = QHBoxLayout()
        self.layout().addLayout(add_key_layout)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter voice command...")
        add_key_layout.addWidget(self.command_input)
        
        # This button will now only display the binding, not trigger listening
        self.binding_display_button = QPushButton("Press a key or click a mouse button")
        self.binding_display_button.setEnabled(False) # Make it unclickable
        add_key_layout.addWidget(self.binding_display_button)

        # --- Buttons to Start Listening ---
        listener_button_layout = QHBoxLayout()
        self.key_listen_button = QPushButton("Bind Keyboard Key")
        self.key_listen_button.clicked.connect(self.start_key_listen)
        listener_button_layout.addWidget(self.key_listen_button)
        
        # 1. Add a new button specifically for mouse input
        self.mouse_listen_button = QPushButton("Bind Mouse Button")
        self.mouse_listen_button.clicked.connect(self.start_mouse_listen)
        listener_button_layout.addWidget(self.mouse_listen_button)
        self.layout().addLayout(listener_button_layout)
        
        # --- State Flags and Data Storage ---
        self.is_listening_for_key = False
        self.is_listening_for_mouse = False # 2. Add a flag for mouse listening
        self.current_binding_str = ""
        
        # --- Add/Remove Buttons ---
        add_button = QPushButton("Add/Update Keybind")
        add_button.clicked.connect(self.add_keybind)
        self.layout().addWidget(add_button)

        remove_button = QPushButton("Remove Selected Keybind")
        remove_button.clicked.connect(self.remove_keybind)
        self.layout().addWidget(remove_button)

        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(0)
        jsonTable = {}
        for command, binding in self.key_bindings.items():
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(command))
            self.table.setItem(row_position, 1, QTableWidgetItem(str(binding)))
            jsonTable[command] = binding
        with open(keybindingsJsonPath,"w") as f:
            json.dump(jsonTable, f, indent=4)

    def start_key_listen(self):
        """Prepares the widget to listen for a single key press."""
        self.binding_display_button.setText("Press a key...")
        self.is_listening_for_key = True
        self.is_listening_for_mouse = False # Ensure other listeners are off
        self.setFocus()

    # 3. Add a function to start listening for mouse clicks
    def start_mouse_listen(self):
        """Prepares the widget to listen for a single mouse click."""
        self.binding_display_button.setText("Click a mouse button...")
        self.is_listening_for_mouse = True
        self.is_listening_for_key = False # Ensure other listeners are off
        self.setFocus()

    def keyPressEvent(self, event):
        if self.is_listening_for_key:
            # ... (key handling logic remains the same)
            key_code = event.key()
            key_text = event.text()
            key_map = {
                Qt.Key.Key_Shift: "Shift", Qt.Key.Key_Control: "Ctrl",
                Qt.Key.Key_Alt: "Alt", Qt.Key.Key_Meta: "Cmd",
                Qt.Key.Key_Tab: "Tab", Qt.Key.Key_Backspace: "Backspace",
                Qt.Key.Key_Return: "Enter"
            }
            if Qt.Key.Key_Space <= key_code <= Qt.Key.Key_ydiaeresis:
                self.current_binding_str = key_text
            else:
                self.current_binding_str = key_map.get(key_code, f"Keycode {key_code}")
            
            self.binding_display_button.setText(self.current_binding_str)
            self.is_listening_for_key = False
        else:
            super().keyPressEvent(event)

    # 4. Implement the mousePressEvent handler
    def mousePressEvent(self, event):
        """This method is called by PyQt when a mouse button is pressed."""
        if self.is_listening_for_mouse:
            button = event.button()
            
            # Map the mouse button enum to a user-friendly string
            mouse_map = {
                Qt.MouseButton.LeftButton: "LMB",
                Qt.MouseButton.RightButton: "RMB",
                Qt.MouseButton.MiddleButton: "MMB",
                Qt.MouseButton.BackButton: "Mouse 4 (Back)",
                Qt.MouseButton.ForwardButton: "Mouse 5 (Fwd)"
            }
            self.current_binding_str = mouse_map.get(button, f"Mouse Btn {button}")

            self.binding_display_button.setText(self.current_binding_str)
            self.is_listening_for_mouse = False
        else:
            super().mousePressEvent(event)

    def add_keybind(self):
        command = self.command_input.text()
        if self.current_binding_str and command:
            self.key_bindings[command] = self.current_binding_str
            self.refresh_table()
            self.command_input.clear()
            self.binding_display_button.setText("Press a key or click a mouse button")
            self.current_binding_str = ""

    def remove_keybind(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            command_to_remove = self.table.item(selected_row, 0).text()
            if command_to_remove in self.key_bindings:
                del self.key_bindings[command_to_remove]
                self.refresh_table()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    data = None
    try:
        with open(keybindingsJsonPath,'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print('keybinds.json not found')
    except json.JSONDecodeError:
         print("Error: Invalid JSON format in 'keybindings.json'.")
    window = KeybindMenu(data)
    window.show()
    sys.exit(app.exec())