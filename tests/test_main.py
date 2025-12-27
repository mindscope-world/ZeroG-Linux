import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import queue

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main

class TestMain(unittest.TestCase):

    @patch('main.mlx_whisper')
    @patch('main.sd.InputStream')
    def setUp(self, mock_sd, mock_whisper):
        # Mock the model warmup so it doesn't actually load during tests
        # We need to mock mlx_whisper.transcribe inside the __init__
        with patch('main.mlx_whisper.transcribe'):
            self.recorder = main.AudioRecorder()

    def test_recorder_initial_state(self):
        self.assertFalse(self.recorder.recording)
        self.assertIsInstance(self.recorder.audio_queue, queue.Queue)

    @patch('main.sd.InputStream')
    @patch('main.subprocess.Popen')
    def test_start_recording(self, mock_popen, mock_sd):
        self.recorder.start_recording()
        self.assertTrue(self.recorder.recording)
        self.assertFalse(self.recorder.q_pressed_during_session)
        mock_sd.assert_called_once()
        mock_popen.assert_called_once()

    @patch('main.sd.InputStream')
    def test_stop_recording(self, mock_sd):
        self.recorder.recording = True
        self.recorder.stream = MagicMock()
        
        with patch('main.threading.Thread') as mock_thread:
            self.recorder.stop_recording()
            self.assertFalse(self.recorder.recording)
            self.recorder.stream.stop.assert_called_once()
            self.recorder.stream.close.assert_called_once()
            mock_thread.assert_called_once()

    @patch('main.mlx_whisper.transcribe')
    @patch('main.pyperclip.copy')
    @patch('main.subprocess.run')
    def test_transcribe_and_type_no_gemini(self, mock_run, mock_copy, mock_transcribe):
        # Mock transcription result
        mock_transcribe.return_value = {"text": "Hello world"}
        
        # Add dummy audio data to queue
        self.recorder.audio_queue.put(MagicMock())
        
        self.recorder.transcribe_and_type(use_gemini=False)
        
        mock_copy.assert_called_with("Hello world")
        mock_run.assert_called() # AppleScript call

if __name__ == '__main__':
    unittest.main()
