# tests/test_main.py
import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import queue
import numpy as np
from zerog.core.state import AppState

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zerog.core.recorder import AudioRecorder

class TestAudioRecorderLinux(unittest.TestCase):

    @patch('zerog.core.recorder.WhisperModel') # Mocking Faster-Whisper
    @patch('zerog.core.recorder.sd.InputStream')
    @patch('zerog.core.recorder.threading.Thread')
    def setUp(self, mock_thread, mock_sd, mock_whisper):
        with patch('zerog.core.recorder.state_machine'):
            self.recorder = AudioRecorder()

    def test_recorder_initial_state(self):
        self.assertFalse(self.recorder.recording)
        self.assertIsInstance(self.recorder.audio_queue, queue.Queue)

    @patch('zerog.core.recorder.state_machine')
    @patch('zerog.core.recorder.sd.InputStream')
    @patch('zerog.core.recorder.subprocess.run')
    def test_start_recording_linux(self, mock_run, mock_sd, mock_state_machine):
        """Verify Linux start sequence: Sound trigger (paplay) and InputStream."""
        from zerog.core.state import AppState
        mock_state_machine.current_state = AppState.RECORDING
        
        self.recorder.start_recording()
        
        self.assertTrue(self.recorder.recording)
        
        # Verify Linux sound playback (paplay) was attempted
        mock_run.assert_called()
        args, _ = mock_run.call_args
        self.assertIn("paplay", args[0])
        
        mock_sd.assert_called_once()

    @patch('zerog.core.recorder.sd.InputStream')
    def test_stop_recording_linux(self, mock_sd):
        self.recorder.recording = True
        mock_stream = MagicMock()
        self.recorder.stream = mock_stream
        
        with patch('zerog.core.recorder.threading.Thread') as mock_thread:
            self.recorder.stop_recording(use_gemini=False)
            
            self.assertFalse(self.recorder.recording)
            self.assertIsNone(self.recorder.stream)
            
            # Transcription and cleanup threads spawned
            self.assertGreaterEqual(mock_thread.call_count, 1)

    @patch('zerog.core.typer.FastTyper.inject') 
    # @patch('zerog.core.recorder.state_machine')
    def test_transcribe_and_type_linux_flow(self, mock_state_machine, mock_inject):
        """Verify Linux-specific injection call using FastTyper.inject."""
        # 1. Mock the Whisper Model transcription
        self.recorder.model = MagicMock()
        mock_segment = MagicMock()
        mock_segment.text = "Hello world"
        self.recorder.model.transcribe.return_value = ([mock_segment], None)
        
        # 2. Mock audio data in queue
        self.recorder.audio_queue.put(np.zeros(1024))
        
        # 3. Action
        self.recorder.transcribe_and_type(use_gemini=False)
        
        # 4. Assert injection was called with transcribed text
        mock_inject.assert_called_once_with("Hello world")
        mock_state_machine.set_state.assert_any_call(AppState.SUCCESS)

    def test_recorder_callback_audio_levels(self, *args):
        """Verify audio levels are calculated and broadcasted."""
        with patch('zerog.core.recorder.state_machine') as mock_sm:
            indata = np.full((1024, 1), 0.1, dtype=np.float32)
            self.recorder.recording = True
            
            self.recorder.callback(indata, 1024, {}, None)
            
            self.assertFalse(self.recorder.audio_queue.empty())
            # RMS logic check: broadcast_audio_level should be called
            self.assertTrue(mock_sm.broadcast_audio_level.called)

    @patch('zerog.core.recorder.state_machine')
    def test_silence_detection_linux(self, mock_state_machine):
        """Verify automatic silence-cutoff triggers PROCESSING state."""
        # Setup silent input
        indata_silent = np.full((1024, 1), 0.001, dtype=np.float32)
        self.recorder.recording = True
        
        # Start silence tracking
        self.recorder.callback(indata_silent, 1024, {}, None)
        self.assertIsNotNone(self.recorder._silence_start_time)
        
        # Simulate passing 11 seconds
        import time
        self.recorder._silence_start_time = time.time() - 11.0
        
        with patch('zerog.core.recorder.threading.Thread') as mock_thread:
            self.recorder.callback(indata_silent, 1024, {}, None)
            
            # Check for transition to PROCESSING
            self.assertTrue(self.recorder._triggered_silence_stop)
            # Find the state machine call in thread targets
            called_set_state = False
            for call in mock_thread.call_args_list:
                if call[1]['target'] == mock_state_machine.set_state:
                    if call[1]['args'][0] == AppState.PROCESSING:
                        called_set_state = True
            self.assertTrue(called_set_state)

if __name__ == '__main__':
    unittest.main()