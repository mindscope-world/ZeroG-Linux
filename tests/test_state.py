import unittest
from unittest.mock import MagicMock
import threading
import time
from macdictate.core.state import StateMachine, AppState

class TestStateMachine(unittest.TestCase):
    def setUp(self):
        # Reset singleton for testing (this is hacky but necessary for singleton testing)
        if StateMachine._instance:
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

    def test_no_notification_if_same_state_no_data(self):
        observer = MagicMock()
        self.sm.add_observer(observer)
        
        self.sm.set_state(AppState.IDLE) # Already IDLE
        observer.assert_not_called()

    def test_notification_same_state_with_data(self):
        observer = MagicMock()
        self.sm.add_observer(observer)
        
        self.sm.set_state(AppState.IDLE, error="Test") # Same state, new data
        observer.assert_called_once_with(AppState.IDLE, {'error': "Test"})

    def test_audio_level_observer_registration(self):
        observer = MagicMock()
        self.sm.add_audio_level_observer(observer)
        
        self.sm.broadcast_audio_level(0.5)
        
        observer.assert_called_once_with(0.5)

    def test_audio_level_observer_removal(self):
        observer = MagicMock()
        self.sm.add_audio_level_observer(observer)
        self.sm.remove_audio_level_observer(observer)
        
        self.sm.broadcast_audio_level(0.5)
        
        observer.assert_not_called()

    def test_audio_level_multiple_observers(self):
        observer1 = MagicMock()
        observer2 = MagicMock()
        self.sm.add_audio_level_observer(observer1)
        self.sm.add_audio_level_observer(observer2)
        
        self.sm.broadcast_audio_level(0.75)
        
        observer1.assert_called_once_with(0.75)
        observer2.assert_called_once_with(0.75)
