import numpy as np
import sounddevice as sd
import pyperclip
import mlx_whisper
import logging
import os
from pathlib import Path
import Cocoa
import Quartz
import time
import queue
import threading
import subprocess
from .state import state_machine, AppState
from . import gemini
import sys
import gc

logger = logging.getLogger(__name__)

# Constants
HF_MODEL_PATH = "mlx-community/distil-whisper-large-v3"

SAMPLE_RATE = 16000
SOUND_FILE = "/System/Library/Sounds/Pop.aiff"
SILENCE_THRESHOLD = 0.015  # RMS amplitude below which is considered silence
SILENCE_DURATION = 5.0    # Seconds of silence to trigger auto-stop
MODEL_UNLOAD_TIMEOUT = 300 # Unload model after 5 minutes of inactivity

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.audio_queue = queue.Queue()
        self.stream = None
        self._lock = threading.Lock()
        self.reset_timer = None
        self._model_dir = None  # Cached resolved model path
        self._preloaded_sound = None  # Pre-loaded sound effect
        self._preloaded_sound = None  # Pre-loaded sound effect
        self._preloaded_sound = None  # Pre-loaded sound effect
        self._processing_start_time = None  # For latency tracking
        
        # Model Unloading Timer
        self._unload_timer = None
        
        # Silence detection
        self._silence_start_time = None
        self._triggered_silence_stop = False
        
        state_machine.add_observer(self.on_state_change)
        threading.Thread(target=self._initialize_all, daemon=True).start()

    def _warmup_audio_subsystem(self):
        """Pre-initialize audio input to eliminate cold-start delay."""
        try:
            # Create a short-lived stream to warm up sounddevice/CoreAudio
            warmup_stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1)
            warmup_stream.start()
            time.sleep(0.1)  # Brief activation to fully initialize
            warmup_stream.stop()
            warmup_stream.close()
            logger.info("Audio subsystem warmup complete.")
        except Exception as e:
            logger.warning(f"Audio warmup failed: {e}")
        
        # Pre-load the sound effect (must run on main thread for Cocoa)
        try:
            self._preloaded_sound = Cocoa.NSSound.soundNamed_("Pop")
            if self._preloaded_sound:
                logger.info("Sound effect pre-loaded.")
        except Exception as e:
            logger.warning(f"Sound preload failed: {e}")

    def _initialize_all(self):
        """Initialize audio subsystem and models in background."""
        # Warmup audio first (faster, unblocks recording quickly)
        self._warmup_audio_subsystem()
        # Then load the Whisper model
        self._initialize_models()

    def _initialize_models(self):
        # Resolve model path (prefer local)
        model_path_str = self._resolve_model_path()
        
        logger.info(f"Loading MLX Whisper Model ({model_path_str})...")
        try:
            if os.path.exists(model_path_str):
                self._model_dir = model_path_str
                model_dir = Path(model_path_str)

            else:
                from huggingface_hub import snapshot_download
                model_dir = Path(snapshot_download(model_path_str))
                self._model_dir = str(model_dir)  # Cache for reuse
            
            weights_path = model_dir / "weights.safetensors"
            model_path_file = model_dir / "model.safetensors"
            
            if not weights_path.exists() and model_path_file.exists():
                logger.info("Creating symlink for mlx_whisper compatibility")
                try:
                    os.symlink(model_path_file, weights_path)
                except FileExistsError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to create symlink: {e}")

            warmup_audio = np.zeros(16000, dtype=np.float32)
            mlx_whisper.transcribe(
                warmup_audio, 
                path_or_hf_repo=self._model_dir,
                language="en",
                initial_prompt="The user is dictating. Valid English text."
            )
            logger.info("Whisper Warmup Complete.")
        except Exception as e:
            logger.error(f"Model initialization failed: {e}", exc_info=True)
            self._handle_error("Model Init Failed")

    def unload_model(self):
        """Unload the MLX Whisper model from memory."""
        try:
            # mlx_whisper.transcribe is a function, so we access the module via sys.modules
            # to reach the ModelHolder class designed for caching
            if "mlx_whisper.transcribe" in sys.modules:
                model_holder = sys.modules["mlx_whisper.transcribe"].ModelHolder
                if model_holder.model is not None:
                    logger.info("Unloading Whisper model to free memory...")
                    model_holder.model = None
                    import mlx.core as mx
                    try:
                         mx.clear_cache()
                    except AttributeError:
                         mx.metal.clear_cache()
                    gc.collect()
                    logger.info("Whisper model unloaded.")
        except Exception as e:
            logger.error(f"Failed to unload model: {e}")

    def _schedule_unload(self):
        """Schedule model unload after timeout."""
        self._cancel_unload()
        self._unload_timer = threading.Timer(MODEL_UNLOAD_TIMEOUT, self.unload_model)
        self._unload_timer.start()

    def _cancel_unload(self):
        """Cancel pending model unload."""
        if self._unload_timer:
            self._unload_timer.cancel()

            self._unload_timer = None

    def _resolve_model_path(self):
        """Check for local model, fallback to HF."""
        # Check standard local location relative to this file
        # zerog/core/recorder.py -> zerog/core -> zerog -> root -> mlx_models
        local_path = Path(__file__).parent.parent.parent / "mlx_models" / "distil-large-v3-4-bit"
        if local_path.exists():
            return str(local_path)
        return HF_MODEL_PATH

    def on_state_change(self, state, data):
        if state == AppState.RECORDING:
            self.start_recording()
        elif state == AppState.PROCESSING:
            use_gemini = data.get('use_gemini', False)
            self.stop_recording(use_gemini)

    def play_sound(self):
        # Use pre-loaded sound for instant playback, fallback to loading fresh
        sound = self._preloaded_sound or Cocoa.NSSound.soundNamed_("Pop")
        if sound:
            sound.play()
        else:
            subprocess.Popen(["afplay", SOUND_FILE])

    def callback(self, indata, frames, time_info, status):
        if self.recording:
            self.audio_queue.put(indata.copy())
            # Calculate RMS level for waveform visualization (0.0 - 1.0)
            rms = np.sqrt(np.mean(indata**2))
            
            # DEBUG: Verify we have signal
            # import sys
            # if rms > 0.01: sys.stderr.write(f"RMS: {rms:.4f}\n")

            # Normalize to 0-1 range (typical speech RMS is 0.01-0.1)
            level = float(min(1.0, rms * 10))
            # Broadcast audio level to HUD via state machine
            state_machine.broadcast_audio_level(level)

            # --- Silence Detection ---
            if rms < SILENCE_THRESHOLD:
                if self._silence_start_time is None:
                    self._silence_start_time = time.time()
                elif (time.time() - self._silence_start_time) > SILENCE_DURATION:
                    if not self._triggered_silence_stop:
                        logger.info(f"Silence detected (> {SILENCE_DURATION}s). Stopping recording.")
                        self._triggered_silence_stop = True
                        # Trigger state change in a separate thread to avoid blocking audio callback
                        use_gemini = state_machine.context.get('use_gemini', False)
                        threading.Thread(target=state_machine.set_state, args=(AppState.PROCESSING,), kwargs={'use_gemini': use_gemini}, daemon=True).start()
            else:
                # Reset silence timer if we hear sound
                self._silence_start_time = None

    def start_recording(self):
        if self.reset_timer:
            self.reset_timer.cancel()
            self.reset_timer = None
            
        # Cancel any pending unload when we start using the model
        self._cancel_unload()

        with self._lock:
            if self.recording: 
                return
            if state_machine.current_state != AppState.RECORDING:
                logger.warning("State changed before recording could start, aborting")
                return
                
            logger.info("Starting Recording...")
            self.recording = True
            
            # Reset silence logic
            self._silence_start_time = None
            self._triggered_silence_stop = False
            
            self.audio_queue = queue.Queue()
            self.play_sound()
            
            try:
                self.stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=self.callback)
                logger.info("Initializing audio stream...")
                self.stream.start()
                logger.info("Audio stream started successfully.")
            except Exception as e:
                logger.error(f"Failed to start stream: {e}", exc_info=True)
                self.recording = False
                self._handle_error("Mic Error")

    def stop_recording(self, use_gemini):
        with self._lock:
            if not self.recording: 
                return
            self.recording = False
            active_stream = self.stream
            self.stream = None

        self._processing_start_time = time.time()  # Track when user released control
        logger.info(f"Stopping Recording. Gemini={use_gemini}")
        
        # Define cleanup function for background thread
        def _cleanup_stream(stream_to_close):
            if stream_to_close:
                try:
                    # Blocking calls moved off main/event thread
                    stream_to_close.stop()
                    stream_to_close.close()
                    logger.info("Audio stream stopped and closed in background.")
                except Exception as e:
                    logger.error(f"Error closing stream: {e}")

        # Start cleanup in daemon thread
        threading.Thread(target=_cleanup_stream, args=(active_stream,), daemon=True).start()
        
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

            # Optimized batch drain - collect all chunks at once
            collect_start = time.time()
            audio_data = []
            while True:
                try:
                    audio_data.append(self.audio_queue.get_nowait())
                except queue.Empty:
                    break
            
            if not audio_data:
                state_machine.set_state(AppState.IDLE)
                return

            # Efficient array creation using vstack (faster than concatenate for many small arrays)
            audio_np = np.vstack(audio_data).flatten()
            collect_duration = time.time() - collect_start
            logger.info(f"Collected {len(audio_data)} chunks in {collect_duration*1000:.1f}ms. Shape: {audio_np.shape}")
            
            start_t = time.time()

            with self._lock:
                # Use resolved model path
                model_path = self._model_dir if self._model_dir else self._resolve_model_path()
                result = mlx_whisper.transcribe(
                    audio_np, 
                    path_or_hf_repo=model_path,
                    language="en",
                    initial_prompt="The user is dictating. Valid English text."
                )
            
            whisper_duration = time.time() - start_t
            text = result["text"].strip()
            logger.info(f"Whisper finished ({whisper_duration:.2f}s): {text}")
            
            if text:
                if use_gemini:
                   logger.info("Starting Gemini processing...")
                   text = gemini.process_text(text)
                   logger.info("Gemini finished.")
                
                # Inject text FIRST (before UI update) to minimize perceived latency
                inject_start = time.time()
                self.inject_text(text)
                inject_duration = time.time() - inject_start
                if self._processing_start_time:
                    total_latency = time.time() - self._processing_start_time
                    logger.info(f"Text injected in {inject_duration*1000:.1f}ms (total {total_latency*1000:.0f}ms from key release)")
                else:
                    logger.info(f"Text injected in {inject_duration*1000:.1f}ms")
                
                # Then update UI (non-blocking)
                state_machine.set_state(AppState.SUCCESS)
                
                if self.reset_timer: 
                    self.reset_timer.cancel()
                self.reset_timer = threading.Timer(2.0, lambda: state_machine.set_state(AppState.IDLE))
                self.reset_timer.start()
            else:
                logger.info("Whisper returned empty text.")
                state_machine.set_state(AppState.IDLE)
            
            # Schedule unload after successful processing
            self._schedule_unload()

        except Exception as e:
            logger.error(f"Transcription Error: {e}", exc_info=True)
            self._handle_error("Processing Failed")
            # Also schedule unload on error to not leave it hanging
            self._schedule_unload()

    def _handle_error(self, message):
        state_machine.set_state(AppState.ERROR, error=message)
        
        if self.reset_timer: 
            self.reset_timer.cancel()
            
        self.reset_timer = threading.Timer(3.0, lambda: state_machine.set_state(AppState.IDLE))
        self.reset_timer.start()

    def inject_text(self, text):
        from .typer import FastTyper
        from .clipboard import ClipboardManager

        # Strategy A: Fast Typing (Universal, Safe)
        # Use for short-to-medium text where typing speed is acceptable.
        # This is the most compatible method as it works at the HID level.
        if len(text) < 1000:
            if FastTyper.type_text(text):
                return
            logger.warning("FastTyper failed, falling back to clipboard injection.")

        # Strategy B: Clipboard Injection (Fallback / Bulk)
        # 1. Snapshot current clipboard
        # 2. Copy new text
        # 3. Paste
        # 4. Restore original clipboard (async)
        
        try:
            snapshot = ClipboardManager.snapshot()
            
            pyperclip.copy(text)
            # Short sleep to ensure clipboard update propagates
            time.sleep(0.05)
            
            # Simulate Cmd+V
            try:
                cmd_down = Quartz.CGEventCreateKeyboardEvent(None, 0x37, True)
                Quartz.CGEventSetFlags(cmd_down, Quartz.kCGEventFlagMaskCommand)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, cmd_down)
                
                v_down = Quartz.CGEventCreateKeyboardEvent(None, 0x09, True)
                Quartz.CGEventSetFlags(v_down, Quartz.kCGEventFlagMaskCommand)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, v_down)
                
                v_up = Quartz.CGEventCreateKeyboardEvent(None, 0x09, False)
                Quartz.CGEventSetFlags(v_up, Quartz.kCGEventFlagMaskCommand)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, v_up)

                cmd_up = Quartz.CGEventCreateKeyboardEvent(None, 0x37, False)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, cmd_up)
            except Exception:
                subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'])

            # Scheduled restoration of the user's original clipboard
            if snapshot:
                threading.Timer(0.6, lambda: ClipboardManager.restore(snapshot)).start()
                
        except Exception as e:
            logger.error(f"Injection failed: {e}", exc_info=True)

