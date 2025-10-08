from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt

class SettingsPage(QWidget):
    """
    A page for application settings, such as microphone gain.
    """
    def __init__(self, vosk_worker, parent=None):
        super().__init__(parent)
        self.vosk_worker = vosk_worker

        layout = QVBoxLayout(self)

        # --- Mic Gain Slider ---
        gain_group_layout = QHBoxLayout()
        gain_label = QLabel("Mic Gain:")
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setRange(0, 300)      # Represents 0% to 300%
        self.gain_slider.setValue(100)         # Default to 100%
        self.gain_slider.setToolTip("Adjust microphone input volume (100% is default)")
        
        gain_group_layout.addWidget(gain_label)
        gain_group_layout.addWidget(self.gain_slider)
        
        # Add the gain slider group to the main layout
        layout.addLayout(gain_group_layout)

        # Add a stretch to push the settings to the top
        layout.addStretch()

        # --- Connections ---
        self.gain_slider.valueChanged.connect(self.vosk_worker.set_gain)