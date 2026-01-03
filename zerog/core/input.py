import time
import threading
import Quartz
from .state import state_machine, AppState
import logging

logger = logging.getLogger(__name__)

KEY_CODE_CTRL = 59
KEY_CODE_Q = 12
POLL_INTERVAL = 0.05
MAX_RECORDING_SECONDS = 120  # 2-minute safety timeout to prevent stuck state

class KeyMonitor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True
        self.was_pressed = False
        self.q_pressed_during_session = False
        self.recording_start_time = None  # Track when recording started for timeout

    def is_key_pressed(self, keycode):
        # 0 = kCGEventSourceStateCombinedSessionState (Combined hardware + software)
        # 1 = kCGEventSourceStateHIDSystemState (Hardware only)
        # Using 0 is generally safer for app-level monitoring as it reflects what the OS "thinks".
        return Quartz.CGEventSourceKeyState(0, keycode)

    def run(self):
        logger.info("KeyMonitor started.")
        while self.running:
            try:
                current_state = state_machine.current_state
                
                # Check Control Key
                is_ctrl_pressed = self.is_key_pressed(KEY_CODE_CTRL)

                # State: IDLE -> RECORDING
                if is_ctrl_pressed and not self.was_pressed:
                    if current_state == AppState.IDLE or current_state == AppState.SUCCESS or current_state == AppState.ERROR:
                        self.q_pressed_during_session = False
                        # Reset context for new session
                        state_machine.context['use_gemini'] = False
                        self.recording_start_time = time.time()  # Start timeout timer
                        state_machine.set_state(AppState.RECORDING)
                        self.was_pressed = True
                
                # State: RECORDING (Check for Q and timeout)
                elif is_ctrl_pressed and self.was_pressed:
                    if current_state == AppState.RECORDING:
                        # Check for Q key
                        if not self.q_pressed_during_session and self.is_key_pressed(KEY_CODE_Q):
                            self.q_pressed_during_session = True
                            state_machine.context['use_gemini'] = True
                        
                        # Check for recording timeout (safety valve)
                        if self.recording_start_time and (time.time() - self.recording_start_time) > MAX_RECORDING_SECONDS:
                            logger.warning(f"Recording timeout ({MAX_RECORDING_SECONDS}s) - forcing transition to PROCESSING")
                            state_machine.set_state(AppState.PROCESSING, use_gemini=self.q_pressed_during_session)
                            self.was_pressed = False
                            self.recording_start_time = None
                
                # State: RECORDING -> PROCESSING
                elif not is_ctrl_pressed and self.was_pressed:
                    if current_state == AppState.RECORDING:
                        state_machine.set_state(AppState.PROCESSING, use_gemini=self.q_pressed_during_session)
                    
                    self.was_pressed = False
                    self.recording_start_time = None  # Reset timeout timer
                
                time.sleep(POLL_INTERVAL)
            except Exception as e:
                logger.error(f"KeyMonitor Error: {e}")
                time.sleep(1) # Backoff
    
    def stop(self):
        self.running = False
