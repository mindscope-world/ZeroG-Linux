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

# --- Configuration & Constants ---
# The AI model used for transcription. "base" is a good balance of speed and accuracy.
MODEL_PATH = "mlx-community/whisper-base-mlx"
# Audio recording settings
SAMPLE_RATE = 16000
# The sound played when recording starts
SOUND_FILE = "/System/Library/Sounds/Pop.aiff"
# Key codes for the hotkeys (59 = Left Control, 12 = Q)
KEY_CODE_CTRL = 59 
KEY_CODE_Q = 12
# How often to check if keys are pressed (in seconds)
POLL_INTERVAL = 0.05
# --- Privacy & Logging ---
# If ENABLE_LOGGING is set to True, the app will save status messages and 
# transcriptions to the local file: mac_dictate.log
# IMPORTANT: All logging (mac_dictate.log) stays on your machine. 
# (Note: Using the optional 'Q' hotkey sends text to Google Gemini in the cloud).
ENABLE_LOGGING = False 

# --- Logging Setup ---
# This sets up where the program writes its status messages (logs).
logger = logging.getLogger(__name__)
if ENABLE_LOGGING:
    # If logging is on, save messages to 'mac_dictate.log' in the project folder
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mac_dictate.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
else:
    # If logging is off, only show critical errors to keep the file clean
    logging.basicConfig(level=logging.CRITICAL) 

class AudioRecorder:
    """Handles recording audio from the microphone and processing it with AI."""
    
    def __init__(self):
        self.recording = False
        self.audio_queue = queue.Queue() # Stores audio data chunks as they come in
        self.stream = None
        self.q_pressed_during_session = False
        
        logger.info(f"Loading MLX Whisper Model ({MODEL_PATH})...")
        logger.info("Warming up model to compile shaders (this takes a moment)...")
        
        # --- Model Warmup ---
        # MLX (Apple's AI framework) compiles code when first used.
        # We run a tiny bit of silent audio through it now so that the 
        # FIRST time you dictate, there isn't a delay.
        warmup_audio = np.zeros(16000, dtype=np.float32)
        try:
            mlx_whisper.transcribe(warmup_audio, path_or_hf_repo=MODEL_PATH)
            logger.info("Model Warmup Complete. Ready. (Hold Left Control)")
        except Exception as e:
            logger.error(f"Warmup failed (check internet connection for model download?): {e}", exc_info=True)

    def play_sound(self):
        """Plays a system sound to notify the user that recording has started."""
        subprocess.Popen(["afplay", SOUND_FILE])

    def callback(self, indata, frames, time, status):
        """This function is called by the audio library whenever new sound data is captured."""
        if self.recording:
            # Add the new audio data to our queue for later processing
            self.audio_queue.put(indata.copy())

    def start_recording(self):
        """Initializes and starts the audio recording stream."""
        if self.recording: return 
        logger.info("Listening...")
        self.recording = True
        self.q_pressed_during_session = False
        self.audio_queue = queue.Queue() # Reset the audio storage
        self.play_sound()
        
        # Create an input stream from the microphone
        self.stream = sd.InputStream(samplerate=SAMPLE_RATE, 
                                     channels=1, 
                                     callback=self.callback)
        self.stream.start()

    def stop_recording(self):
        """Stops the recording stream and triggers transcription."""
        if not self.recording: return
        logger.info("Processing...")
        
        # Determine if we should use Gemini based on whether 'Q' was held
        use_gemini = self.q_pressed_during_session
        
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        # Process the captured audio in a background thread so the main loop
        # stays responsive for the next dictation.
        threading.Thread(
            target=self.transcribe_and_type, 
            args=(use_gemini,), 
            daemon=True
        ).start()

    def transcribe_and_type(self, use_gemini=False):
        """Converts audio to text and sends it to the active window."""
        if self.audio_queue.empty():
            return

        # Combine all the small chunks of audio into one big array
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())
        
        audio_np = np.concatenate(audio_data, axis=0).flatten()
        
        # --- Step 1: Whisper Transcription (Audio -> Text) ---
        start_t = time.time()
        result = mlx_whisper.transcribe(
            audio_np, 
            path_or_hf_repo=MODEL_PATH
        )
        whisper_duration = time.time() - start_t
        
        text = result["text"].strip()
        
        if text:
            logger.info(f"Whisper Transcription ({whisper_duration:.2f}s): {text}")
            
            # --- Step 2: Gemini Post-Processing (Optional Editing) ---
            # Only run if 'Q' was held AND a Gemini API key is configured
            if use_gemini and gemini_processor.IS_CONFIGURED:
                start_t = time.time()
                # Use Gemini to clean up the text (grammar, tone, etc.)
                processed_text = gemini_processor.process_text(text)
                gemini_duration = time.time() - start_t
                
                if processed_text != text:
                    logger.info(f"Gemini Processed ({gemini_duration:.2f}s): {processed_text}")
                    text = processed_text
            elif use_gemini and not gemini_processor.IS_CONFIGURED:
                logger.warning("Gemini was requested (Q held) but no API key is configured. Skipping.")
            else:
                logger.info("Gemini processing skipped (Q not held).")
            
            # --- Step 3: Injection (Paste to Screen) ---
            self.inject_text(text)
        else:
            logger.info("No speech detected.")

    def inject_text(self, text):
        """Copies text to the clipboard and simulates Command+V to paste it."""
        pyperclip.copy(text)
        # Wait a tiny bit for the computer to recognize the clipboard change
        time.sleep(0.05) 
        # Use AppleScript to tell the system to press Command+V
        subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'])

def is_key_pressed(keycode):
    """Checks if a specific key on the keyboard is currently held down."""
    return Quartz.CGEventSourceKeyState(1, keycode)

if __name__ == "__main__":
    # This is the entry point of the script
    recorder = AudioRecorder()
    was_pressed = False

    try:
        # Main loop: keep running forever (until stopped)
        while True:
            # Check if User is holding the Control Key
            is_pressed = is_key_pressed(KEY_CODE_CTRL)
            
            if is_pressed and not was_pressed:
                # User just pressed the key: Start recording
                recorder.start_recording()
                was_pressed = True
            
            elif is_pressed and was_pressed:
                # User is still holding Control: Check if they also press 'Q'
                if not recorder.q_pressed_during_session and is_key_pressed(KEY_CODE_Q):
                    recorder.q_pressed_during_session = True
            
            elif not is_pressed and was_pressed:
                # User let go of Control: Stop recording and process
                recorder.stop_recording()
                was_pressed = False
            
            # Sleep for a tiny bit to prevent the CPU from working too hard
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        # Handle the user pressing Ctrl+C in the terminal
        logger.info("Exiting...")