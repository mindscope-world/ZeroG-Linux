import time
import queue
import subprocess
import threading
import numpy as np
import sounddevice as sd
import pyperclip
import mlx_whisper
import Quartz 
import os
import logging
import gemini_processor

# Options: "mlx-community/whisper-tiny-mlx", "mlx-community/whisper-small-mlx"
MODEL_PATH = "mlx-community/whisper-base-mlx"
SAMPLE_RATE = 16000
SOUND_FILE = "/System/Library/Sounds/Pop.aiff"
KEY_CODE_CTRL = 59 
KEY_CODE_Q = 12
POLL_INTERVAL = 0.05
ENABLE_LOGGING = True # Set to True to enable debug logging to file

# Setup logging
logger = logging.getLogger(__name__)
if ENABLE_LOGGING:
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mac_dictate.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
else:
    logging.basicConfig(level=logging.CRITICAL) # Suppress non-critical logs

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.audio_queue = queue.Queue()
        self.stream = None
        self.q_pressed_during_session = False
        
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
        self.q_pressed_during_session = False
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
        
        # Use the flag tracked during the session
        use_gemini = self.q_pressed_during_session
        
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        self.transcribe_and_type(use_gemini=use_gemini)

    def transcribe_and_type(self, use_gemini=False):
        if self.audio_queue.empty():
            return

        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())
        
        # Flatten into a single float32 numpy array
        audio_np = np.concatenate(audio_data, axis=0).flatten()
        
        # --- MLX TRANSCRIPTION ---
        start_t = time.time()
        result = mlx_whisper.transcribe(
            audio_np, 
            path_or_hf_repo=MODEL_PATH
        )
        whisper_duration = time.time() - start_t
        
        text = result["text"].strip()
        
        if text:
            logger.info(f"Whisper Transcription ({whisper_duration:.2f}s): {text}")
            
            if use_gemini:
                # --- GEMINI POST-PROCESSING ---
                start_t = time.time()
                processed_text = gemini_processor.process_text(text)
                gemini_duration = time.time() - start_t
                
                if processed_text != text:
                    logger.info(f"Gemini Processed ({gemini_duration:.2f}s): {processed_text}")
                    text = processed_text
            else:
                logger.info("Gemini processing skipped (Q not held).")
            
            self.inject_text(text)
        else:
            logger.info("No speech detected.")

    def inject_text(self, text):
        pyperclip.copy(text)
        # Minimal delay to ensure clipboard update (50ms is usually imperceptible but safe)
        time.sleep(0.05) 
        # Use AppleScript for robust pasting without long delays
        subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'])

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
            
            elif is_pressed and was_pressed:
                # Continuous polling for Q while recording
                if not recorder.q_pressed_during_session and is_key_pressed(KEY_CODE_Q):
                    recorder.q_pressed_during_session = True
            
            elif not is_pressed and was_pressed:
                recorder.stop_recording()
                was_pressed = False
            
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Exiting...")