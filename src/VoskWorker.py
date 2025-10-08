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
        
        self.can_guess = True
        

    @pyqtSlot(dict)
    def initialize(self, keybindings : dict):
        """Loads the model. This is called once when the thread starts."""
    
        
        try:
            print("Loading Vosk model and setting grammar...")
            macro_commands = list(keybindings.keys())
            
            # --- This is the crucial fix ---
            # Only load the heavy model from disk if it hasn't been loaded before.
            if not self.model:
                self.model = Model(self.model_path, lang="en-us")

            # This part is lightweight and can be run every time to update the grammar.
            if len(macro_commands) > 0:
                self.recognizer = KaldiRecognizer(self.model, 16000,json.dumps(macro_commands))
            else:
                self.recognizer = KaldiRecognizer(self.model,16000)
            self.recognizer.SetWords(True)
            self.modelReady.emit(True, "Model loaded successfully with current profile.")
            
        except Exception as e:
            # Emit modelReady signal on failure to update the UI correctly
            self.modelReady.emit(False, f"Error loading model: {e}")

    def audio_callback(self, indata, frames, time, status):
        """This is called by sounddevice for each audio chunk."""
        CONFIDENCE_THRESHOLD = 0.75
        
        if status:
            print(status, file=sys.stderr)
        
        if self.is_listening and self.recognizer:
            if self.recognizer.AcceptWaveform(bytes(indata)):
                result_json = json.loads(self.recognizer.Result())
                print(f"Final result: {result_json}")
                if 'result' in result_json:
                    words = result_json['result']
                    
                    # Calculate the average confidence of all words in the phrase
                    total_confidence = sum(word['conf'] for word in words)
                    average_confidence = total_confidence / len(words)
                    
                    text = result_json.get('text', '')

                    # For debugging: print the text and its confidence
                    print(f"'{text}' (Confidence: {average_confidence:.2f})")
                    
                    # Only emit the signal if confidence is high enough
                    if average_confidence >= CONFIDENCE_THRESHOLD and self.can_guess:
                        self.textRecognized.emit(text)
                    self.can_guess = True
            else:
                partial_result_json = json.loads(self.recognizer.PartialResult())
                
                if partial_result_json.get('partial'):
                    text = partial_result_json['partial']
                    print(f"Partial result: {text}")
                    
                    if self.can_guess:
                        self.textRecognized.emit(text)
                        self.can_guess = False


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