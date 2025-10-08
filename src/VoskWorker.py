import sys
import json
import sounddevice as sd
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QTextEdit
from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from vosk import Model, KaldiRecognizer
import time
import numpy as np

class VoskWorker(QObject):
    textRecognized = pyqtSignal(str)
    modelReady = pyqtSignal(bool,str)

    def __init__(self, model_path):
        super().__init__()
        self.model_path = model_path
        self.model = None
        self.recognizer = None
        self.stream = None
        self.is_listening = False
        self.commands = []
        self.last_command_time = 0
        self.command_cooldown = 0.5 # 500ms cooldown
        self.gain = 1.0 # Default gain is 100%

    @pyqtSlot(int)
    def set_gain(self, gain_percent):
        """Sets the microphone gain factor from a percentage value."""
        self.gain = gain_percent / 100.0
        print(f"Mic gain set to: {self.gain}")

    @pyqtSlot(dict)
    def initialize(self, keybindings : dict):
        """Loads the model and sets the grammar."""
        try:
            print("Loading Vosk model and setting grammar...")
            self.commands = list(keybindings.keys())

            if not self.model:
                self.model = Model(self.model_path, lang="en-us")

            if len(self.commands) > 0:
                grammar = json.dumps(self.commands)
                self.recognizer = KaldiRecognizer(self.model, 16000, grammar)
            else:
                self.recognizer = KaldiRecognizer(self.model, 16000)

            self.recognizer.SetWords(True)
            self.modelReady.emit(True, "Model loaded successfully with current profile.")

        except Exception as e:
            self.modelReady.emit(False, f"Error loading model: {e}")

    def audio_callback(self, indata, frames, time_info, status):
        """This is called by sounddevice for each audio chunk."""
        if status:
            print(status, file=sys.stderr)

        # Apply gain and prevent clipping
        amplified_data = indata * self.gain
        clipped_data = np.clip(amplified_data, -32768, 32767).astype(np.int16)

        if self.is_listening and self.recognizer:
            if self.recognizer.AcceptWaveform(bytes(clipped_data)):
                result_json = json.loads(self.recognizer.Result())
                text = result_json.get('text', '')
                if text:
                    print(f"Final result: '{text}'")
                    current_time = time.time()
                    if text in self.commands and (current_time - self.last_command_time > self.command_cooldown):
                         self.textRecognized.emit(text)
                         self.last_command_time = current_time
            else:
                partial_result_json = json.loads(self.recognizer.PartialResult())
                partial_text = partial_result_json.get('partial', '')
                if partial_text:
                    print(f"Partial result: {partial_text}")
                    current_time = time.time()
                    # Check if any of the known commands are present in the partial text
                    for command in self.commands:
                        if command in partial_text and (current_time - self.last_command_time > self.command_cooldown):
                            print(f"Partial command matched: {command}")
                            self.textRecognized.emit(command)
                            self.last_command_time = current_time
                            # **THE FIX IS HERE**: Use Reset() instead of recreating the object
                            self.recognizer.Reset()
                            break # Exit loop after finding the first command


    @pyqtSlot()
    def start_listening(self):
        """Starts the audio stream."""
        if self.is_listening or not self.recognizer:
            return
        print("Starting listening...")
        self.is_listening = True
        self.stream = sd.InputStream(
            callback=self.audio_callback,
            channels=1,
            samplerate=16000,
            dtype='int16',
            latency='low'
        )
        self.stream.start()

    @pyqtSlot()
    def stop_listening(self):
        """Stops the audio stream."""
        if not self.is_listening:
            return
        print("Stopping listening.")
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.is_listening = False