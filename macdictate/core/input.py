import time
import threading
import Quartz
from .state import state_machine, AppState
import logging

logger = logging.getLogger(__name__)

KEY_CODE_CTRL = 59
KEY_CODE_Q = 12
POLL_INTERVAL = 0.05

class KeyMonitor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True
        self.was_pressed = False
        self.q_pressed_during_session = False

    def is_key_pressed(self, keycode):
        return Quartz.CGEventSourceKeyState(1, keycode)

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
                        state_machine.set_state(AppState.RECORDING)
                        self.was_pressed = True
                
                # State: RECORDING (Check for Q)
                elif is_ctrl_pressed and self.was_pressed:
                    if current_state == AppState.RECORDING:
                        if not self.q_pressed_during_session and self.is_key_pressed(KEY_CODE_Q):
                            self.q_pressed_during_session = True
                            # Optional: Notify UI that Q was detected?
                            # For now, we just store it.
                
                # State: RECORDING -> PROCESSING
                elif not is_ctrl_pressed and self.was_pressed:
                    if current_state == AppState.RECORDING:
                        state_machine.set_state(AppState.PROCESSING, use_gemini=self.q_pressed_during_session)
                    
                    self.was_pressed = False
                
                time.sleep(POLL_INTERVAL)
            except Exception as e:
                logger.error(f"KeyMonitor Error: {e}")
                time.sleep(1) # Backoff
    
    def stop(self):
        self.running = False
