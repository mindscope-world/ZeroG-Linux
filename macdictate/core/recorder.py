import time
import queue
import threading
import subprocess
import numpy as np
import sounddevice as sd
import pyperclip
import mlx_whisper
import logging
from .state import state_machine, AppState
from . import gemini

logger = logging.getLogger(__name__)

# Constants
MODEL_PATH = "mlx-community/whisper-base-mlx"
SAMPLE_RATE = 16000
SOUND_FILE = "/System/Library/Sounds/Pop.aiff"

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.audio_queue = queue.Queue()
        self.stream = None
        self._lock = threading.Lock()
        
        # Subscribe to state changes
        state_machine.add_observer(self.on_state_change)
        
        # Start initialization in background to not block app start
        threading.Thread(target=self._initialize_models, daemon=True).start()

    def _initialize_models(self):
        logger.info(f"Loading MLX Whisper Model ({MODEL_PATH})...")
        try:
            # Warmup Whisper
            warmup_audio = np.zeros(16000, dtype=np.float32)
            mlx_whisper.transcribe(warmup_audio, path_or_hf_repo=MODEL_PATH)
            logger.info("Whisper Warmup Complete.")
            
            # Warmup Gemini (uses the function we moved to macdictate.core.gemini)
            # We need to expose warmup in gemini.py or just call process_text with dummy?
            # Existing gemini.py runs warmup on import/init.
            pass
        except Exception as e:
            logger.error(f"Model initialization failed: {e}", exc_info=True)
            state_machine.set_state(AppState.ERROR, error="Model Init Failed")

    def on_state_change(self, state, data):
        """Handle state transitions."""
        if state == AppState.RECORDING:
            self.start_recording()
        elif state == AppState.PROCESSING:
            use_gemini = data.get('use_gemini', False)
            self.stop_recording(use_gemini)

    def play_sound(self):
        subprocess.Popen(["afplay", SOUND_FILE])

    def callback(self, indata, frames, time, status):
        if self.recording:
            self.audio_queue.put(indata.copy())

    def start_recording(self):
        if self.recording: return
        logger.info("Starting Recording...")
        self.recording = True
        self.audio_queue = queue.Queue()
        self.play_sound()
        
        try:
            self.stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=self.callback)
            self.stream.start()
        except Exception as e:
            logger.error(f"Failed to start stream: {e}")
            state_machine.set_state(AppState.ERROR, error="Mic Error")

    def stop_recording(self, use_gemini):
        if not self.recording: return
        logger.info(f"Stopping Recording. Gemini={use_gemini}")
        
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # Offload processing to specific worker thread
        threading.Thread(
            target=self.transcribe_and_type, 
            args=(use_gemini,), 
            daemon=True
        ).start()

    def transcribe_and_type(self, use_gemini):
        try:
            logger.info("Transcribe thread started. Checking queue...")
            if self.audio_queue.empty():
                logger.info("Queue empty. Resetting to IDLE.")
                state_machine.set_state(AppState.IDLE)
                return

            audio_data = []
            while not self.audio_queue.empty():
                try:
                    audio_data.append(self.audio_queue.get_nowait())
                except queue.Empty:
                    break
            
            logger.info(f"Collected {len(audio_data)} audio chunks.")
            if not audio_data:
                state_machine.set_state(AppState.IDLE)
                return

            audio_np = np.concatenate(audio_data, axis=0).flatten()
            logger.info(f"Audio array shape: {audio_np.shape}. Starting Whisper...")
            
            start_t = time.time()
            # We enforce a lock here to ensure MLX doesn't get confused if multiple threads existed roughly at once
            # (Though logic prevents it, this is safer)
            with self._lock:
                result = mlx_whisper.transcribe(audio_np, path_or_hf_repo=MODEL_PATH)
            
            whisper_duration = time.time() - start_t
            text = result["text"].strip()
            logger.info(f"Whisper finished ({whisper_duration:.2f}s): {text}")
            
            if text:
                if use_gemini:
                   logger.info("Starting Gemini processing...")
                   text = gemini.process_text(text)
                   logger.info("Gemini finished.")
                
                self.inject_text(text)
                state_machine.set_state(AppState.SUCCESS)
                # Auto-reset to IDLE after a moment? 
                # Or KeyMonitor will trigger IDLE? 
                # Actually, State stays SUCCESS so UI can show checkmark.
                # We need a Timer to reset to IDLE.
                threading.Timer(2.0, lambda: state_machine.set_state(AppState.IDLE)).start()
            else:
                logger.info("Whisper returned empty text.")
                state_machine.set_state(AppState.IDLE)

        except Exception as e:
            logger.error(f"Transcription Error: {e}", exc_info=True)
            state_machine.set_state(AppState.ERROR, error="Processing Failed")
            threading.Timer(3.0, lambda: state_machine.set_state(AppState.IDLE)).start()

    def inject_text(self, text):
        pyperclip.copy(text)
        time.sleep(0.05)
        subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'])
