import numpy as np
import sounddevice as sd
import pyperclip
from faster_whisper import WhisperModel
import logging
import os
from pathlib import Path
import time
import queue
import threading
import subprocess
from .state import state_machine, AppState
from . import gemini
import sys
import gc

logger = logging.getLogger(__name__)

# Constants - Using Faster-Whisper for Linux performance
# Options: "tiny", "base", "small", "medium"
MODEL_SIZE = "medium" 
SAMPLE_RATE = 16000
# Standard Ubuntu path for system sounds; fallbacks included
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
        self.model = None  # WhisperModel instance
        self._processing_start_time = None
        
        # Silence detection
        self._silence_start_time = None
        self._triggered_silence_stop = False
        
        state_machine.add_observer(self.on_state_change)
        threading.Thread(target=self._initialize_all, daemon=True).start()

    def _warmup_audio_subsystem(self):
        """Pre-initialize ALSA/PulseAudio to eliminate cold-start delay."""
        try:
            warmup_stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1)
            warmup_stream.start()
            time.sleep(0.1)
            warmup_stream.stop()
            warmup_stream.close()
            logger.info("Linux Audio subsystem (ALSA/Pulse) warmup complete.")
        except Exception as e:
            logger.warning(f"Audio warmup failed: {e}")

    def _initialize_all(self):
        self._warmup_audio_subsystem()
        self._initialize_models()

    def _initialize_models(self):
        """Loads Faster-Whisper. Auto-detects CUDA (NVIDIA) or CPU."""
        logger.info(f"Loading Faster-Whisper Model ({MODEL_SIZE})...")
        try:
            # Determine device (Use 'cuda' if you have an NVIDIA GPU, else 'cpu')
            # compute_type="int8" is the Linux equivalent of 4-bit quantization for speed
            self.model = WhisperModel(MODEL_SIZE, device="auto", compute_type="int8")
            
            # Warmup inference
            warmup_audio = np.zeros(16000, dtype=np.float32)
            self.model.transcribe(warmup_audio, beam_size=1)
            logger.info("Faster-Whisper Warmup Complete.")
        except Exception as e:
            logger.error(f"Model initialization failed: {e}", exc_info=True)
            self._handle_error("Model Init Failed")

    def on_state_change(self, state, data):
        if state == AppState.RECORDING:
            self.start_recording()
        elif state == AppState.PROCESSING:
            use_gemini = data.get('use_gemini', False)
            self.stop_recording(use_gemini)

    def play_sound(self):
        """Linux-native sound playback using paplay (PulseAudio) or aplay."""
        try:
            if os.path.exists(SOUND_FILE):
                subprocess.Popen(["paplay", SOUND_FILE], stderr=subprocess.DEVNULL)
            else:
                # Fallback to system beep if file not found
                subprocess.Popen(["beep"], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def callback(self, indata, frames, time_info, status):
        if self.recording:
            self.audio_queue.put(indata.copy())
            rms = np.sqrt(np.mean(indata**2))
            level = float(min(1.0, rms * 10))
            state_machine.broadcast_audio_level(level)

            # Silence Detection
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
        if self.reset_timer:
            self.reset_timer.cancel()
            self.reset_timer = None

        with self._lock:
            if self.recording: return
            
            logger.info("Starting Recording...")
            self.recording = True
            self._silence_start_time = None
            self._triggered_silence_stop = False
            self.audio_queue = queue.Queue()
            self.play_sound()
            
            try:
                self.stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=self.callback)
                self.stream.start()
            except Exception as e:
                logger.error(f"Failed to start stream: {e}")
                self.recording = False
                self._handle_error("Mic Error")

    def stop_recording(self, use_gemini):
        with self._lock:
            if not self.recording: return
            self.recording = False
            active_stream = self.stream
            self.stream = None

        self._processing_start_time = time.time()
        
        def _cleanup_stream(stream_to_close):
            if stream_to_close:
                stream_to_close.stop()
                stream_to_close.close()

        threading.Thread(target=_cleanup_stream, args=(active_stream,), daemon=True).start()
        threading.Thread(target=self.transcribe_and_type, args=(use_gemini,), daemon=True).start()

    def transcribe_and_type(self, use_gemini):
        try:
            if self.audio_queue.empty():
                state_machine.set_state(AppState.IDLE)
                return

            audio_data = []
            while True:
                try:
                    audio_data.append(self.audio_queue.get_nowait())
                except queue.Empty:
                    break
            
            audio_np = np.vstack(audio_data).flatten()
            
            # Faster-Whisper Transcription
            segments, info = self.model.transcribe(audio_np, beam_size=5, language="en")
            text = " ".join([segment.text for segment in segments]).strip()
            
            logger.info(f"Transcription: {text}")
            
            if text:
                if use_gemini:
                   text = gemini.process_text(text)
                
                self.inject_text(text)
                state_machine.set_state(AppState.SUCCESS)
                
                if self.reset_timer: self.reset_timer.cancel()
                self.reset_timer = threading.Timer(2.0, lambda: state_machine.set_state(AppState.IDLE))
                self.reset_timer.start()
            else:
                state_machine.set_state(AppState.IDLE)

        except Exception as e:
            logger.error(f"Transcription Error: {e}")
            self._handle_error("Processing Failed")

    def _handle_error(self, message):
        state_machine.set_state(AppState.ERROR, error=message)
        threading.Timer(3.0, lambda: state_machine.set_state(AppState.IDLE)).start()

    def inject_text(self, text):
        """Linux implementation using pyperclip and xdotool."""
        try:
            # 1. Store current clipboard to restore later
            old_clipboard = pyperclip.paste()
            
            # 2. Copy new text
            pyperclip.copy(text)
            time.sleep(0.1) # Linux clipboard sync buffer
            
            # 3. Use xdotool to trigger Ctrl+V (Universal for X11)
            # If you are on Wayland, you may need 'ydotool'
            subprocess.run(["xdotool", "key", "ctrl+v"])
            
            # 4. Restore original clipboard after a delay
            def restore():
                time.sleep(0.5)
                pyperclip.copy(old_clipboard)
            threading.Thread(target=restore, daemon=True).start()
                
        except Exception as e:
            logger.error(f"Injection failed: {e}")