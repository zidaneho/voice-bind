import sys
import json
import sounddevice as sd
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QTextEdit
from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from vosk import Model, KaldiRecognizer


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
        

    @pyqtSlot()
    def initialize(self):
        """Loads the model. This is called once when the thread starts."""
        try:
            print("Loading Vosk model...")
            
            macro_commands = [
                "jump", "reload", "crouch", "sprint", 
                "next weapon", "previous weapon", "use item", 
                "save", "load", "hello", "boo"
            ]
            
            self.model = Model(self.model_path,lang="en-us")
            self.recognizer = KaldiRecognizer(self.model, 16000,json.dumps(macro_commands))
            self.recognizer.SetWords(True)
            self.modelReady.emit(True,"Model loaded successfully")
            
            
        except Exception as e:
            self.textRecognized.emit(f"Error loading model: {e}")

    def audio_callback(self, indata, frames, time, status):
        """This is called by sounddevice for each audio chunk."""
        CONFIDENCE_THRESHOLD = 0.75
        
        if status:
            print(status, file=sys.stderr)
        
        if self.is_listening and self.recognizer:
            if self.recognizer.AcceptWaveform(bytes(indata)):
                result_json = json.loads(self.recognizer.Result())
                if 'result' in result_json:
                    words = result_json['result']
                    
                    # Calculate the average confidence of all words in the phrase
                    total_confidence = sum(word['conf'] for word in words)
                    average_confidence = total_confidence / len(words)
                    
                    text = result_json.get('text', '')

                    # For debugging: print the text and its confidence
                    print(f"'{text}' (Confidence: {average_confidence:.2f})")
                    
                    # Only emit the signal if confidence is high enough
                    if average_confidence >= CONFIDENCE_THRESHOLD:
                        self.textRecognized.emit(text)
                    else:
                        # Optional: let the user know it was ignored
                        print(f"--> Ignored due to low confidence.")


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
        self.is_listening = False