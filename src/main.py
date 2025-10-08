import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget,
    QVBoxLayout, QWidget, QLabel
)
from components.NavMenu import NavMenu
# 1. Import your actual page classes
from pages.VoicePage import VoicePage
from pages.KeybindPage import KeybindPage
from util import settingsJsonPath
from components.ProfileManager import ProfileManager
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoiceBind")
        self.setGeometry(100, 100, 500, 400) # Increased height for better view
        
      
        self.profile_manager = ProfileManager()

        # --- Page Setup ---
        self.stacked_widget = QStackedWidget()
    

        # 2. Instantiate your pages
        self.voice_page = VoicePage(self.profile_manager)
        self.keybind_page = KeybindPage(self.profile_manager)

        # 3. Create the pages dictionary with your real widgets
        #    The keys ("home", "keybinds", "settings") MUST match the
        #    identifiers used in your NavMenu class.
        self.pages = {
            "home": self.voice_page,
            "keybinds": self.keybind_page,
            "settings": QLabel("This is the SETTINGS Page (Not Implemented)")
        }
        for page_widget in self.pages.values():
            self.stacked_widget.addWidget(page_widget)

        # --- Create and Pass the Callback ---
        nav_menu = NavMenu(navigation_callback=self.handle_navigation)

        # --- Main Layout ---
        main_layout = QVBoxLayout()
        main_layout.addWidget(nav_menu)          # Add the nav menu at the top
        main_layout.addWidget(self.stacked_widget) # Add the page area below it

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Start on the home page
        self.handle_navigation("home")

    def handle_navigation(self, page_name: str):
        """This method belongs to MainWindow and does the actual work."""
        target_widget = self.pages.get(page_name)
        if target_widget:
            self.stacked_widget.setCurrentWidget(target_widget)
            print(f"MainWindow switched view to: {page_name}")
        else:
            print(f"Error: Page '{page_name}' not found!")

    def closeEvent(self, event):
        """Ensure the voice recognition thread is stopped cleanly."""
        print("Closing application...")
        self.voice_page.vosk_worker.stop_listening()
        self.voice_page.vosk_thread.quit()
        self.voice_page.vosk_thread.wait()
        event.accept()

# --- Run Application ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())