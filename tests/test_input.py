import unittest
from unittest.mock import MagicMock, patch
from zerog.core.state import AppState

# Import the Linux-compatible KeyMonitor (using pynput)
from zerog.core.input import KeyMonitor

class TestKeyMonitorLinux(unittest.TestCase):
    
    def setUp(self):
        # We patch the state_machine at the module level
        self.patcher = patch('zerog.core.input.state_machine')
        self.mock_sm = self.patcher.start()
        self.monitor = KeyMonitor()
        
        # Define some common key mocks
        self.ctrl_key = MagicMock()
        # In pynput, keyboard.Key.ctrl_l is an enum-like object
        # We'll simulate it by comparing equality in our mocks
        
    def tearDown(self):
        self.patcher.stop()

    def test_on_press_ctrl_starts_recording(self):
        """Test that pressing Left Control transitions IDLE -> RECORDING."""
        from pynput import keyboard
        self.mock_sm.current_state = AppState.IDLE
        
        # Action: Simulate pressing Ctrl_L
        self.monitor.on_press(keyboard.Key.ctrl_l)
        
        # Assertions
        self.assertTrue(self.monitor.ctrl_pressed)
        self.mock_sm.set_state.assert_called_once_with(AppState.RECORDING)
        self.assertIsNotNone(self.monitor.recording_start_time)

    def test_on_press_q_activates_gemini(self):
        from pynput import keyboard
        self.mock_sm.current_state = AppState.RECORDING
        self.monitor.ctrl_pressed = True
        
        # FIX: Initialize the mock context as a real dict so it stores values
        self.mock_sm.context = {'use_gemini': False}
        
        q_key = MagicMock()
        q_key.char = 'q'
        
        self.monitor.on_press(q_key)
        
        self.assertEqual(self.mock_sm.context['use_gemini'], True)

    def test_on_release_ctrl_triggers_processing(self):
        """Test that releasing Ctrl triggers the PROCESSING state."""
        from pynput import keyboard
        self.mock_sm.current_state = AppState.RECORDING
        self.monitor.ctrl_pressed = True
        self.monitor.q_pressed = True # Gemini was toggled
        
        # Action: Release Ctrl_L
        self.monitor.on_release(keyboard.Key.ctrl_l)
        
        # Assertions
        self.assertFalse(self.monitor.ctrl_pressed)
        self.mock_sm.set_state.assert_called_once_with(
            AppState.PROCESSING, 
            use_gemini=True
        )

    def test_safety_timeout(self):
        """Verify the watchdog stops recording if it exceeds MAX_RECORDING_SECONDS."""
        import time
        from zerog.core.input import MAX_RECORDING_SECONDS
        
        self.mock_sm.current_state = AppState.RECORDING
        # Set start time to far in the past
        self.monitor.recording_start_time = time.time() - (MAX_RECORDING_SECONDS + 1)
        self.monitor.running = True
        
        # We manually trigger the internal timeout check logic
        # (Usually this runs in a thread, but we call the logic directly for the test)
        with patch('zerog.core.input.time.sleep', side_effect=[None, Exception("Stop Loop")]):
            try:
                self.monitor._check_timeout()
            except Exception:
                pass # Expected to break the infinite loop
        
        # Assertions
        self.mock_sm.set_state.assert_called_with(AppState.PROCESSING, use_gemini=False)
        self.assertIsNone(self.monitor.recording_start_time)

if __name__ == '__main__':
    unittest.main()