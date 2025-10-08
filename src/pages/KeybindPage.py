import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QComboBox, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt, pyqtSlot

class KeybindPage(QWidget):
    def __init__(self, profile_manager):
        super().__init__()
        self.profile_manager = profile_manager
        self.key_bindings = self.profile_manager.get_keybindings()

        # Connect to the profile manager's signals
        self.profile_manager.profileChanged.connect(self.on_profile_changed)
        self.profile_manager.profilesListChanged.connect(self.update_profile_list)

        self.setWindowTitle("Keybind Menu")
        self.setLayout(QVBoxLayout())

        # --- Profile Management UI ---
        profile_layout = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.update_profile_list(self.profile_manager.get_all_profile_names())
        self.profile_combo.currentTextChanged.connect(self.profile_manager.switch_profile)
        profile_layout.addWidget(self.profile_combo)

        self.create_profile_button = QPushButton("Create New")
        self.create_profile_button.clicked.connect(self.create_profile)
        profile_layout.addWidget(self.create_profile_button)

        self.rename_profile_button = QPushButton("Rename Current")
        self.rename_profile_button.clicked.connect(self.rename_profile)
        profile_layout.addWidget(self.rename_profile_button)

        self.delete_profile_button = QPushButton("Delete Current")
        self.delete_profile_button.clicked.connect(self.delete_profile)
        profile_layout.addWidget(self.delete_profile_button)

        self.layout().addLayout(profile_layout)

        # --- Keybinding Table and Input UI (remains the same) ---
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Command", "Binding"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout().addWidget(self.table)
        add_key_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter voice command...")
        add_key_layout.addWidget(self.command_input)
        self.binding_display_button = QPushButton("Press a key or click a mouse button")
        self.binding_display_button.setEnabled(False)
        add_key_layout.addWidget(self.binding_display_button)
        self.layout().addLayout(add_key_layout)
        listener_button_layout = QHBoxLayout()
        self.key_listen_button = QPushButton("Bind Keyboard Key")
        self.key_listen_button.clicked.connect(self.start_key_listen)
        listener_button_layout.addWidget(self.key_listen_button)
        self.mouse_listen_button = QPushButton("Bind Mouse Button")
        self.mouse_listen_button.clicked.connect(self.start_mouse_listen)
        listener_button_layout.addWidget(self.mouse_listen_button)
        self.layout().addLayout(listener_button_layout)
        self.is_listening_for_key = False
        self.is_listening_for_mouse = False
        self.current_binding_str = ""
        add_button = QPushButton("Add/Update Keybind")
        add_button.clicked.connect(self.add_keybind)
        self.layout().addWidget(add_button)
        remove_button = QPushButton("Remove Selected Keybind")
        remove_button.clicked.connect(self.remove_keybind)
        self.layout().addWidget(remove_button)

        self.refresh_table()

    @pyqtSlot(list)
    def update_profile_list(self, profiles):
        """Updates the profile dropdown list itself."""
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(profiles)
        # Ensure the selection is synchronized after rebuilding the list
        self.profile_combo.setCurrentText(self.profile_manager.get_active_profile_name())
        self.profile_combo.blockSignals(False)

    def create_profile(self):
        text, ok = QInputDialog.getText(self, 'Create Profile', 'Enter profile name:')
        if ok and text:
            self.profile_manager.create_profile(text)

    def rename_profile(self):
        old_name = self.profile_manager.get_active_profile_name()
        if old_name == "default":
            QMessageBox.warning(self, "Warning", "Cannot rename the default profile.")
            return
        text, ok = QInputDialog.getText(self, 'Rename Profile', 'Enter new name:', text=old_name)
        if ok and text and text != old_name:
            self.profile_manager.rename_profile(old_name, text)

    def delete_profile(self):
        profile_name = self.profile_manager.get_active_profile_name()
        if profile_name == "default":
            QMessageBox.warning(self, "Warning", "Cannot delete the default profile.")
            return

        reply = QMessageBox.question(self, 'Delete Profile',
                                     f"Are you sure you want to delete the profile '{profile_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.profile_manager.delete_profile(profile_name)

    @pyqtSlot(dict)
    def on_profile_changed(self, profile_data):
        """
        This slot is called when the active profile changes.
        It updates the keybinding table and ensures the dropdown shows the correct active profile.
        """
        self.key_bindings = profile_data.get("keybindings", {})
        self.refresh_table()
        
        # FIX: Just update the current selection, don't rebuild the whole list.
        # The update_profile_list slot will handle rebuilding when the list itself changes.
        self.profile_combo.blockSignals(True)
        self.profile_combo.setCurrentText(self.profile_manager.get_active_profile_name())
        self.profile_combo.blockSignals(False)

    def refresh_table(self):
        """Populates the table with keybindings."""
        self.table.setRowCount(0)
        if self.key_bindings:
            for command, binding in self.key_bindings.items():
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QTableWidgetItem(command))
                self.table.setItem(row_position, 1, QTableWidgetItem(str(binding)))

    # --- (The rest of the methods for key/mouse listening and adding/removing keybinds remain unchanged) ---
    def start_key_listen(self):
        self.binding_display_button.setText("Press a key...")
        self.is_listening_for_key = True
        self.is_listening_for_mouse = False
        self.setFocus()

    def start_mouse_listen(self):
        self.binding_display_button.setText("Click a mouse button...")
        self.is_listening_for_mouse = True
        self.is_listening_for_key = False
        self.setFocus()
    
    def keyPressEvent(self, event):
        if self.is_listening_for_key:
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

    def mousePressEvent(self, event):
        if self.is_listening_for_mouse:
            button = event.button()
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
        command = self.command_input.text().lower()
        if self.current_binding_str and command:
            self.key_bindings[command] = self.current_binding_str
            self.profile_manager.save_keybindings(self.key_bindings)
            self.command_input.clear()
            self.binding_display_button.setText("Press a key or click a mouse button")
            self.current_binding_str = ""

    def remove_keybind(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            command_to_remove = self.table.item(selected_row, 0).text()
            if command_to_remove in self.key_bindings:
                del self.key_bindings[command_to_remove]
                self.profile_manager.save_keybindings(self.key_bindings)