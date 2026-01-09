import threading
import time
from pynput import keyboard
from zerog.core.state import state_machine, AppState

class KeyMonitor(threading.Thread):
    def __init__(self):
        # Initialize the background thread
        super().__init__()
        self.daemon = True  # Ensures the thread closes when you exit the app
        self.ctrl_pressed = False
        self.q_pressed = False
        self.recording_start_time = 0

    def run(self):
        """
        The entry point for the thread. This starts the listener 
        without blocking the main GUI window.
        """
        # Listen for the generic 'Key.ctrl' found in your debug test
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def on_press(self, key):
        """Handles key down events"""
        try:
            # Detect Left-Control or the generic Control key
            if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl]:
                if not self.ctrl_pressed:
                    self.ctrl_pressed = True
                    self.recording_start_time = time.time()
                    # Trigger the state machine to start recording
                    state_machine.set_state(AppState.RECORDING)
            
            # Detect 'q' while Ctrl is held for AI polishing
            if hasattr(key, 'char') and key.char == 'q' and self.ctrl_pressed:
                self.q_pressed = True
                # Update context to tell the app to use Gemini later
                state_machine.context['use_gemini'] = True
                
        except Exception as e:
            print(f"Error in keyboard on_press: {e}")

    def on_release(self, key):
        """Handles key up events"""
        try:
            # When Control is released, stop recording and start processing
            if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl]:
                self.ctrl_pressed = False
                
                # Move to processing state; pass the 'q' flag for Gemini
                state_machine.set_state(AppState.PROCESSING, use_gemini=self.q_pressed)
                
                # Reset the 'q' toggle for the next session
                self.q_pressed = False
                
        except Exception as e:
            print(f"Error in keyboard on_release: {e}")