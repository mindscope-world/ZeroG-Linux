import numpy as np
import sounddevice as sd
import pyperclip
from faster_whisper import WhisperModel
import logging
import os
import time
import queue
import threading
import subprocess
from .state import state_machine, AppState
from . import gemini

logger = logging.getLogger(__name__)

# Constants optimized for Intel i7-1165G7
MODEL_SIZE = "base"  # Changed from medium to base for speed/reliability
SAMPLE_RATE = 16000
SOUND_FILE = "/usr/share/sounds/freedesktop/stereo/message.oga"
SILENCE_THRESHOLD = 0.015  
SILENCE_DURATION = 5.0    

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.audio_queue = queue.Queue()
        self.stream = None
        self._lock = threading.Lock()
        self.reset_timer = None
        self.model = None 
        self._processing_start_time = None
        
        # Silence detection
        self._silence_start_time = None
        self._triggered_silence_stop = False
        
        state_machine.add_observer(self.on_state_change)
        # Start initialization in a thread to keep GUI responsive
        threading.Thread(target=self._initialize_all, daemon=True).start()

    def _warmup_audio_subsystem(self):
        """Initializes ALSA/PulseAudio early to avoid capture delays."""
        try:
            warmup_stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1)
            warmup_stream.start()
            time.sleep(0.1)
            warmup_stream.stop()
            warmup_stream.close()
            logger.info("Audio subsystem warmed up.")
        except Exception as e:
            logger.warning(f"Audio warmup failed: {e}")

    def _initialize_all(self):
        self._warmup_audio_subsystem()
        self._initialize_models()

    def _initialize_models(self):
        """Loads Faster-Whisper forced to CPU for Linux stability."""
        logger.info(f"Loading Whisper Model ({MODEL_SIZE}) on CPU...")
        try:
            # FORCE CPU: This prevents the 'stuck' behavior on Intel Xe graphics
            # compute_type="int8" is most efficient for 11th Gen i7 CPUs
            self.model = WhisperModel(
                MODEL_SIZE, 
                device="cpu", 
                compute_type="int8",
                cpu_threads=4 # Uses 4 of your 8 threads for balance
            )
            
            # Warmup inference with silence
            warmup_audio = np.zeros(SAMPLE_RATE, dtype=np.float32)
            self.model.transcribe(warmup_audio, beam_size=1)
            logger.info("Whisper ready.")
        except Exception as e:
            logger.error(f"Model Init Failed: {e}")
            self._handle_error("Model Init Failed")

    def on_state_change(self, state, data):
        if state == AppState.RECORDING:
            self.start_recording()
        elif state == AppState.PROCESSING:
            use_gemini = data.get('use_gemini', False) if data else False
            self.stop_recording(use_gemini)

    def play_sound(self):
        """Uses paplay (standard for Ubuntu PulseAudio)."""
        try:
            if os.path.exists(SOUND_FILE):
                subprocess.Popen(["paplay", SOUND_FILE], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def callback(self, indata, frames, time_info, status):
        if self.recording:
            self.audio_queue.put(indata.copy())
            rms = np.sqrt(np.mean(indata**2))
            level = float(min(1.0, rms * 10))
            state_machine.broadcast_audio_level(level)

            if rms < SILENCE_THRESHOLD:
                if self._silence_start_time is None:
                    self._silence_start_time = time.time()
                elif (time.time() - self._silence_start_time) > SILENCE_DURATION:
                    if not self._triggered_silence_stop:
                        self._triggered_silence_stop = True
                        use_gemini = state_machine.context.get('use_gemini', False)
                        threading.Thread(target=state_machine.set_state, 
                                       args=(AppState.PROCESSING,), 
                                       kwargs={'use_gemini': use_gemini}, 
                                       daemon=True).start()
            else:
                self._silence_start_time = None

    def start_recording(self):
        with self._lock:
            if self.recording: return
            self.recording = True
            self._silence_start_time = None
            self._triggered_silence_stop = False
            self.audio_queue = queue.Queue()
            self.play_sound()
            
            try:
                self.stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=self.callback)
                self.stream.start()
            except Exception as e:
                logger.error(f"Mic Error: {e}")
                self.recording = False
                self._handle_error("Mic Error")

    def stop_recording(self, use_gemini):
        with self._lock:
            if not self.recording: return
            self.recording = False
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

        # Kick off transcription in background
        threading.Thread(target=self.transcribe_and_type, args=(use_gemini,), daemon=True).start()

    def transcribe_and_type(self, use_gemini):
        try:
            if self.audio_queue.empty():
                state_machine.set_state(AppState.IDLE)
                return

            # Combine audio chunks
            audio_data = []
            while not self.audio_queue.empty():
                audio_data.append(self.audio_queue.get())
            
            audio_np = np.vstack(audio_data).flatten()
            
            # Transcription Loop
            segments, _ = self.model.transcribe(audio_np, beam_size=5)
            text = " ".join([segment.text for segment in segments]).strip()
            
            if text:
                if use_gemini:
                   text = gemini.process_text(text)
                
                self.inject_text(text)
                state_machine.set_state(AppState.SUCCESS)
                time.sleep(1.5)
            
            state_machine.set_state(AppState.IDLE)

        except Exception as e:
            logger.error(f"Transcription Error: {e}")
            self._handle_error("Processing Failed")

    def _handle_error(self, message):
        state_machine.set_state(AppState.ERROR, error=message)
        threading.Timer(3.0, lambda: state_machine.set_state(AppState.IDLE)).start()

    def inject_text(self, text):
        """Native Linux X11 text injection."""
        try:
            old_clipboard = pyperclip.paste()
            pyperclip.copy(text)
            time.sleep(0.1) 
            subprocess.run(["xdotool", "key", "ctrl+v"])
            
            def restore():
                time.sleep(0.5)
                pyperclip.copy(old_clipboard)
            threading.Thread(target=restore, daemon=True).start()
        except Exception as e:
            logger.error(f"Paste failed: {e}")