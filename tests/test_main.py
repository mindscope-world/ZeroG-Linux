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

    @patch('macdictate.core.recorder.sd.InputStream')
    @patch('macdictate.core.recorder.subprocess.Popen')
    def test_start_recording(self, mock_popen, mock_sd):
        self.recorder.start_recording()
        self.assertTrue(self.recorder.recording)
        mock_sd.assert_called_once()
        mock_popen.assert_called_once()

    @patch('macdictate.core.recorder.sd.InputStream')
    def test_stop_recording(self, mock_sd):
        self.recorder.recording = True
        mock_stream = MagicMock()
        self.recorder.stream = mock_stream
        
        with patch('macdictate.core.recorder.threading.Thread') as mock_thread:
            self.recorder.stop_recording(use_gemini=False) # Updated signature
            self.assertFalse(self.recorder.recording)
            mock_stream.stop.assert_called_once()
            mock_stream.close.assert_called_once()
            mock_thread.assert_called_once()

    @patch('macdictate.core.recorder.mlx_whisper.transcribe')
    @patch('macdictate.core.recorder.pyperclip.copy')
    @patch('macdictate.core.recorder.subprocess.run')
    @patch('macdictate.core.recorder.state_machine')
    def test_transcribe_and_type_no_gemini(self, mock_state_machine, mock_run, mock_copy, mock_transcribe):
        # Mock transcription result
        mock_transcribe.return_value = {"text": "Hello world"}
        
        # Add dummy audio data to queue
        self.recorder.audio_queue.put(MagicMock())
        
        self.recorder.transcribe_and_type(use_gemini=False)
        
        mock_copy.assert_called_with("Hello world")
        mock_run.assert_called() # AppleScript call

if __name__ == '__main__':
    unittest.main()
