import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import queue
import threading

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the new package structure
from macdictate.core.recorder import AudioRecorder

class TestAudioRecorder(unittest.TestCase):

    @patch('macdictate.core.recorder.mlx_whisper')
    @patch('macdictate.core.recorder.sd.InputStream')
    @patch('macdictate.core.recorder.threading.Thread') # Mock thread starting in __init__
    def setUp(self, mock_thread, mock_sd, mock_whisper):
        # We also need to mock state_machine to avoid side effects
        with patch('macdictate.core.recorder.state_machine'):
            self.recorder = AudioRecorder()

    def test_recorder_initial_state(self):
        self.assertFalse(self.recorder.recording)
        self.assertIsInstance(self.recorder.audio_queue, queue.Queue)

    @patch('macdictate.core.recorder.state_machine')
    @patch('macdictate.core.recorder.sd.InputStream')
    @patch('macdictate.core.recorder.Cocoa.NSSound')
    def test_start_recording(self, mock_nssound, mock_sd, mock_state_machine):
        # Mock sound object
        mock_sound_instance = MagicMock()
        mock_nssound.soundNamed_.return_value = mock_sound_instance
        
        # Set state to RECORDING (required due to race condition protection)
        from macdictate.core.state import AppState
        mock_state_machine.current_state = AppState.RECORDING
        
        self.recorder.start_recording()
        
        self.assertTrue(self.recorder.recording)
        
        # Verify sound played
        mock_nssound.soundNamed_.assert_called_with("Pop")
        mock_sound_instance.play.assert_called_once()
        
        mock_sd.assert_called_once()

    @patch('macdictate.core.recorder.sd.InputStream')
    def test_stop_recording(self, mock_sd):
        self.recorder.recording = True
        mock_stream = MagicMock()
        self.recorder.stream = mock_stream
        
        with patch('macdictate.core.recorder.threading.Thread') as mock_thread:
            self.recorder.stop_recording(use_gemini=False)
            self.assertFalse(self.recorder.recording)
            mock_stream.stop.assert_called_once()
            mock_stream.close.assert_called_once()
            mock_thread.assert_called_once()

    @patch('macdictate.core.recorder.mlx_whisper.transcribe')
    @patch('macdictate.core.recorder.pyperclip.copy')
    @patch('macdictate.core.recorder.Quartz')
    @patch('macdictate.core.recorder.state_machine')
    def test_transcribe_and_type_no_gemini(self, mock_state_machine, mock_quartz, mock_copy, mock_transcribe):
        # Mock transcription result
        mock_transcribe.return_value = {"text": "Hello world"}
        
        # Add dummy audio data to queue
        self.recorder.audio_queue.put(MagicMock())
        
        self.recorder.transcribe_and_type(use_gemini=False)
        
        mock_copy.assert_called_with("Hello world")
        # Verify Quartz was used for cmd+v
        mock_quartz.CGEventCreateKeyboardEvent.assert_called()
        mock_quartz.CGEventPost.assert_called()

    @patch('macdictate.core.recorder.state_machine')
    def test_recorder_callback(self, mock_state_machine):
        # Create a dummy audio buffer (numpy array)
        import numpy as np
        indata = np.full((1024, 1), 0.1, dtype=np.float32)
        frames = 1024
        time_info = {}
        status = None
        
        # Must be recording to process audio
        self.recorder.recording = True
        
        self.recorder.callback(indata, frames, time_info, status)
        
        # Verify queue put
        self.assertFalse(self.recorder.audio_queue.empty())
        
        # Verify broadcast
        # RMS of 0.1 is 0.1. Level = min(1.0, 0.1 * 10) = 1.0
        mock_state_machine.broadcast_audio_level.assert_called_with(1.0)

if __name__ == '__main__':
    unittest.main()


