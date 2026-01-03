import unittest
from unittest.mock import MagicMock, patch
import time
from zerog.core.state import AppState

# We need to mock Quartz properly since it might not exist in test env or we want to control it
# But we import KeyMonitor which imports Quartz.
# If Quartz is not installed in the environment running tests (it is here), it's fine.
# We will patch it regardless.

from zerog.core.input import KeyMonitor, KEY_CODE_CTRL, KEY_CODE_Q

class TestKeyMonitor(unittest.TestCase):
    
    @patch('zerog.core.input.Quartz.CGEventSourceKeyState')
    @patch('zerog.core.input.state_machine')
    def test_run_idle_to_recording(self, mock_state_machine, mock_key_state):
        monitor = KeyMonitor()
        monitor.running = True
        
        # Setup: State is IDLE
        mock_state_machine.current_state = AppState.IDLE
        
        # Scenario: Ctrl Pressed
        # 1. First poll: Not pressed
        # 2. Second poll: Pressed -> Transition to RECORDING
        # 3. Third poll: Pressed -> No change
        # 4. Stop
        
        # Note: KeyMonitor.run loop is infinite. We need to inject a way to break it or test logic differently.
        # Since we can't easily break the while loop without modifying code, 
        # let's test the logic pieces if possible, or threading approach with a side_effect that stops it.
        
        # Testing logic step-by-step by extracting logic would be better, but refactoring not allowed by prompt "just organization".
        # So we will subclass or just run one iteration logic? 
        # Actually, let's just make the loop condition run once.
        
        # Better: run is a loop. Let's patch 'time.sleep' to raise an exception to break the loop? 
        # Or set monitor.running = False in a side_effect of something called inside loop.
        
        # Logic test:
        # Loop 1: Ctrl pressed.
        def key_side_effect(state, keycode):
            if keycode == KEY_CODE_CTRL:
                return True
            return False
        mock_key_state.side_effect = key_side_effect
        
        # We need to test the logic INSIDE run.
        # Let's extract the body of the loop for testing if we could, but we can't refactor.
        # So we will run the thread for a tiny bit? No, that's flaky.
        
        # Alternative: We can mock 'state_machine.current_state' property.
        
        # Let's try to verify the logic by calling a single pass manual simulation 
        # OR by setting running=False after the first pass via a mock side effect.
        
        pass

    # A better approach for `test_input.py` without refactoring `run()`:
    # We can rely on `time.sleep` being called at the end of the loop.
    # We patch `time.sleep` to set `self.running = False`.
    
    @patch('zerog.core.input.state_machine')
    @patch('zerog.core.input.Quartz.CGEventSourceKeyState')
    @patch('zerog.core.input.time.sleep')
    def test_transition_idle_to_recording(self, mock_sleep, mock_key_state, mock_sm):
        monitor = KeyMonitor()
        mock_sm.current_state = AppState.IDLE
        
        # Ctrl is pressed
        mock_key_state.side_effect = lambda s, k: True if k == KEY_CODE_CTRL else False
        
        # Run loop once
        def stop_loop(*args):
            monitor.running = False
        mock_sleep.side_effect = stop_loop
        
        monitor.run()
        
        mock_sm.set_state.assert_called_once_with(AppState.RECORDING)
        self.assertTrue(monitor.was_pressed)

    @patch('zerog.core.input.state_machine')
    @patch('zerog.core.input.Quartz.CGEventSourceKeyState')
    @patch('zerog.core.input.time.sleep')
    def test_transition_recording_to_processing(self, mock_sleep, mock_key_state, mock_sm):
        monitor = KeyMonitor()
        
        # Setup: Already recording and was_pressed=True (user holding info)
        monitor.was_pressed = True
        mock_sm.current_state = AppState.RECORDING
        
        # Ctrl is released
        mock_key_state.return_value = False
        
        def stop_loop(*args):
            monitor.running = False
        mock_sleep.side_effect = stop_loop
        
        monitor.run()
        
        # Should transition to PROCESSING with gemini=False (default)
        mock_sm.set_state.assert_called_once_with(AppState.PROCESSING, use_gemini=False)
        self.assertFalse(monitor.was_pressed)

    @patch('zerog.core.input.state_machine')
    @patch('zerog.core.input.Quartz.CGEventSourceKeyState')
    @patch('zerog.core.input.time.sleep')
    def test_transition_recording_with_q(self, mock_sleep, mock_key_state, mock_sm):
        monitor = KeyMonitor()
        monitor.was_pressed = True
        mock_sm.current_state = AppState.RECORDING
        
        # Scenario: Ctrl Pressed AND Q Pressed
        # We need two iterations here? 
        # Iteration 1: Ctrl + Q pressed -> sets q_pressed_during_session
        # Iteration 2: Ctrl Released -> triggers processing with gemini=True
        
        # We can implement a side_effect dealing with multiple calls to KeyState and Sleep.
        
        # KeyState calls: 
        # Iter 1: Check Ctrl (True), Check Q (True)
        # Iter 2: Check Ctrl (False)
        
        # Sequence of calls to CGEventSourceKeyState:
        # 1. (Iter 1) Ctrl -> True
        # 2. (Iter 1) Q -> True
        # 3. (Iter 2) Ctrl -> False
        
        key_responses = [True, True, False] # Ctrl, Q, Ctrl(released)
        
        def key_side_effect(state, keycode):
            if not key_responses: return False
            val = key_responses.pop(0)
            return val
            
        mock_key_state.side_effect = key_side_effect
        
        # Sleep calls: control loop count
        # Sleep 1: Continue
        # Sleep 2: Stop
        sleep_counts = [0]
        def sleep_side_effect(*args):
            sleep_counts[0] += 1
            if sleep_counts[0] >= 2:
                monitor.running = False
        mock_sleep.side_effect = sleep_side_effect
        
        monitor.run()
        
        # Verify
        mock_sm.set_state.assert_called_with(AppState.PROCESSING, use_gemini=True)

if __name__ == '__main__':
    unittest.main()
