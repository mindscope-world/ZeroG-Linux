import unittest
from unittest.mock import MagicMock
import threading
import time
from zerog.core.state import StateMachine, AppState

class TestStateMachine(unittest.TestCase):
    def setUp(self):
        # Reset singleton for clean testing slate
        StateMachine._instance = None
        self.sm = StateMachine()

    def test_singleton(self):
        sm1 = StateMachine()
        sm2 = StateMachine()
        self.assertIs(sm1, sm2)

    def test_initial_state(self):
        self.assertEqual(self.sm.current_state, AppState.IDLE)

    def test_set_state_transition(self):
        self.sm.set_state(AppState.RECORDING)
        self.assertEqual(self.sm.current_state, AppState.RECORDING)

    def test_observer_notification(self):
        observer = MagicMock()
        self.sm.add_observer(observer)
        
        self.sm.set_state(AppState.PROCESSING, use_gemini=True)
        observer.assert_called_once_with(AppState.PROCESSING, {'use_gemini': True})

    def test_audio_level_broadcasting(self):
        observer = MagicMock()
        self.sm.add_audio_level_observer(observer)
        self.sm.broadcast_audio_level(0.85)
        observer.assert_called_once_with(0.85)

    def test_thread_safety_stress(self):
        """
        Verify that multiple threads updating the state machine 
        simultaneously (common in ZeroG Linux) don't cause race conditions.
        """
        observer = MagicMock()
        self.sm.add_observer(observer)
        
        def rapid_updates():
            for _ in range(100):
                self.sm.set_state(AppState.RECORDING)
                self.sm.set_state(AppState.IDLE)

        threads = [threading.Thread(target=rapid_updates) for _ in range(5)]
        
        for t in threads: t.start()
        for t in threads: t.join()

        # Ensure the system remains stable and observers were called
        self.assertTrue(observer.called)
        self.assertIn(self.sm.current_state, [AppState.IDLE, AppState.RECORDING])

if __name__ == '__main__':
    unittest.main()