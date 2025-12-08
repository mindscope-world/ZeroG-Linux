import time
import queue
import subprocess
import threading
import numpy as np
import sounddevice as sd
import pyperclip
import pyautogui
import mlx_whisper
import Quartz 
import os
import logging

# Setup logging to file in the script's directory
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mac_dictate.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# MLX models are pulled from HuggingFace. 
# "mlx-community/whisper-base-mlx" is a solid balance of speed/accuracy.
# Options: "mlx-community/whisper-tiny-mlx", "mlx-community/whisper-small-mlx"
MODEL_PATH = "mlx-community/whisper-base-mlx"
SAMPLE_RATE = 16000
SOUND_FILE = "/System/Library/Sounds/Breeze.aiff"
KEY_CODE_CTRL = 59 
POLL_INTERVAL = 0.05

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.audio_queue = queue.Queue()
        self.stream = None
        
        logger.info(f"Loading MLX Whisper Model ({MODEL_PATH})...")
        logger.info("Warming up model to compile shaders (this takes a moment)...")
        
        # --- WARM UP ---
        # MLX compiles lazily. We run a dummy transcription so the first
        # real user dictation doesn't have a 2-second lag.
        warmup_audio = np.zeros(16000, dtype=np.float32)
        try:
            mlx_whisper.transcribe(warmup_audio, path_or_hf_repo=MODEL_PATH)
            logger.info("Model Warmup Complete. Ready. (Hold Left Control)")
        except Exception as e:
            logger.error(f"Warmup failed (check internet connection for model download?): {e}", exc_info=True)

    def play_sound(self):
        subprocess.Popen(["afplay", SOUND_FILE])

    def callback(self, indata, frames, time, status):
        if self.recording:
            self.audio_queue.put(indata.copy())

    def start_recording(self):
        if self.recording: return 
        logger.info("Listening...")
        self.recording = True
        self.audio_queue = queue.Queue()
        self.play_sound()
        
        # sounddevice produces float32 by default, which MLX handles natively
        self.stream = sd.InputStream(samplerate=SAMPLE_RATE, 
                                     channels=1, 
                                     callback=self.callback)
        self.stream.start()

    def stop_recording(self):
        if not self.recording: return
        logger.info("Processing...")
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        self.transcribe_and_type()

    def transcribe_and_type(self):
        if self.audio_queue.empty():
            return

        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())
        
        # Flatten into a single float32 numpy array
        audio_np = np.concatenate(audio_data, axis=0).flatten()
        
        # --- MLX TRANSCRIPTION ---
        # direct numpy array support
        result = mlx_whisper.transcribe(
            audio_np, 
            path_or_hf_repo=MODEL_PATH
        )
        
        text = result["text"].strip()
        
        if text:
            logger.info(f"Detected: {text}")
            self.inject_text(text)
        else:
            logger.info("No speech detected.")

    def inject_text(self, text):
        pyperclip.copy(text)
        time.sleep(0.1)
        with pyautogui.hold('command'):
            pyautogui.press('v')

def is_key_pressed(keycode):
    """Polls hardware state of specific key (Left Ctrl = 59)"""
    return Quartz.CGEventSourceKeyState(1, keycode)

if __name__ == "__main__":
    recorder = AudioRecorder()
    was_pressed = False

    try:
        while True:
            is_pressed = is_key_pressed(KEY_CODE_CTRL)
            
            if is_pressed and not was_pressed:
                recorder.start_recording()
                was_pressed = True
            
            elif not is_pressed and was_pressed:
                recorder.stop_recording()
                was_pressed = False
            
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Exiting...")