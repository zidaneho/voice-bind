# NavMenu.py (or in the same file)
from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout

class NavMenu(QWidget):
    def __init__(self, navigation_callback, parent=None):
        """
        A reusable navigation menu widget.
        - navigation_callback: A function that will be called with a
                               page name (str) when a button is clicked.
        """
        super().__init__(parent)
        
        # We store the callback function but the NavMenu itself
        # has no idea what that function actually does.
        self.navigate = navigation_callback

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0) # Remove extra space

        # Create buttons
        home_button = QPushButton("Home")
        keybinds_button = QPushButton("Keybinds")
        settings_button = QPushButton("Settings")

        # Connect the button signals to the provided callback
        home_button.clicked.connect(lambda: self.navigate("home"))
        keybinds_button.clicked.connect(lambda: self.navigate("keybinds"))
        settings_button.clicked.connect(lambda: self.navigate("settings"))
        
        # Add buttons to the layout
        layout.addWidget(home_button)
        layout.addWidget(keybinds_button)
        layout.addWidget(settings_button)

        self.setLayout(layout)