import sys
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar, QStackedWidget, QHBoxLayout, QVBoxLayout, QPushButton
from pages.VoicePage import VoicePage
from pages.KeybindPage import KeybindPage

# --- Main Application Window ---
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("VoiceBind")
        self.setGeometry(100, 100, 400, 200)
        
       
        stacked_widget =  QStackedWidget()
        self.voice_page = VoicePage()
        self.keybind_page = KeybindPage()
        
        stacked_widget.addWidget(self.voice_page)
        stacked_widget.addWidget(self.keybind_page)
        
        nav_menu = QVBoxLayout()
        self.voiceBindButton = QPushButton("Click Me")
        self.voiceBindButton
        nav_menu.add(voiceBindButton)
        
        
        
        layout = QHBoxLayout()
        layout.addWidget(nav_menu)
        layout.addWidget(stacked_widget)
        
        
        
        
        
        self.setCentralWidget(layout)
        
        
        
        
        
        button_action = QAction("Your button", self)
        button_action.setStatusTip("This is your button")
        button_action.triggered.connect(self.toolbar_button_clicked)
        button_action.setCheckable(True)
    
        
        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        file_menu.addAction(button_action)

    def toolbar_button_clicked(self, s):
        print("click", s)

    def closeEvent(self, event):
        """Ensure the thread is stopped cleanly."""
        self.voice_page.vosk_worker.stop_listening()
        self.voice_page.vosk_thread.quit()
        self.voice_page.vosk_thread.wait()
        event.accept()

# --- Run the Application ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())