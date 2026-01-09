import numpy as np
import sounddevice as sd
import pyperclip
from faster_whisper import WhisperModel
import time
import queue
import threading
import subprocess
from .state import state_machine, AppState

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.audio_queue = queue.Queue()
        self.stream = None
        
        # Exact settings from your successful debug_model.py
        print("🛠️  Loading Whisper 'tiny' (float32)...")
        self.model = WhisperModel("tiny", device="cpu", compute_type="float32")
        print("✅ Recorder Engine Ready.")
        
        state_machine.add_observer(self.on_state_change)

    def on_state_change(self, state, data=None):
        if state == AppState.RECORDING:
            self.start_recording()
        elif state == AppState.PROCESSING:
            # Fixed: handle case where data might be None
            use_gemini = data.get('use_gemini', False) if data else False
            self.stop_recording(use_gemini)

    def start_recording(self):
        print("🎤 Recording...")
        self.recording = True
        self.audio_queue = queue.Queue()
        self.stream = sd.InputStream(samplerate=16000, channels=1, callback=self.callback)
        self.stream.start()

    def callback(self, indata, frames, time_info, status):
        if self.recording:
            self.audio_queue.put(indata.copy())

    def stop_recording(self, use_gemini):
        print("⏹️  Processing...")
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        # Run transcription in a background thread to keep GUI responsive
        threading.Thread(target=self.transcribe, args=(use_gemini,), daemon=True).start()

    def transcribe(self, use_gemini):
        try:
            audio_data = []
            while not self.audio_queue.empty():
                audio_data.append(self.audio_queue.get())
            
            if not audio_data:
                state_machine.set_state(AppState.IDLE)
                return

            audio_np = np.vstack(audio_data).flatten()
            segments, _ = self.model.transcribe(audio_np, beam_size=1)
            text = " ".join([s.text for s in segments]).strip()
            
            print(f"📝 Result: {text}")
            
            if text:
                pyperclip.copy(text)
                # Ensure xdotool is installed: sudo apt install xdotool
                subprocess.run(["xdotool", "key", "ctrl+v"])
                state_machine.set_state(AppState.SUCCESS)
                time.sleep(2)
            
            state_machine.set_state(AppState.IDLE)
        except Exception as e:
            print(f"❌ Transcription Error: {e}")
            state_machine.set_state(AppState.IDLE)