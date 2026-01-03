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
            self.assertIsNone(self.recorder.stream)
            
            # Should spawn 2 threads: one for cleanup, one for transcription
            self.assertEqual(mock_thread.call_count, 2)
            
            # Find the cleanup thread (the one with the stream arg)
            call_args_list = mock_thread.call_args_list
            cleanup_call = None
            for call in call_args_list:
                args, kwargs = call
                if 'args' in kwargs and len(kwargs['args']) > 0 and kwargs['args'][0] == mock_stream:
                    cleanup_call = call
                    break
            
            self.assertIsNotNone(cleanup_call, "Cleanup thread not spawned")
            
            # Manually run the cleanup target to verify it closes the stream
            cleanup_target = cleanup_call[1]['target']
            cleanup_args = cleanup_call[1]['args']
            cleanup_target(*cleanup_args)
            
            mock_stream.stop.assert_called_once()
            mock_stream.close.assert_called_once()

    @patch('macdictate.core.recorder.mlx_whisper.transcribe')
    @patch('macdictate.core.recorder.state_machine')
    def test_transcribe_and_type_no_gemini(self, mock_state_machine, mock_transcribe):
        # We need to mock the local imports inside inject_text
        with patch('macdictate.core.typer.FastTyper.type_text') as mock_type_text, \
             patch('macdictate.core.clipboard.ClipboardManager') as mock_clipboard:
            
            # Setup mock to return True for typing success
            mock_type_text.return_value = True
            
            # Mock transcription result "Hello world" (length 11 < 1000)
            mock_transcribe.return_value = {"text": "Hello world"}
            
            # Add dummy audio data to queue
            self.recorder.audio_queue.put(MagicMock())
            
            # Action
            self.recorder.transcribe_and_type(use_gemini=False)
            
            # Assert
            # Should choose FastTyper path for short text
            mock_type_text.assert_called_with("Hello world")
            # Should NOT fallback to clipboard
            mock_clipboard.snapshot.assert_not_called()
    
    @patch('macdictate.core.recorder.mlx_whisper.transcribe')
    @patch('macdictate.core.recorder.state_machine')
    @patch('macdictate.core.recorder.pyperclip.copy')
    def test_transcribe_long_text_fallback(self, mock_copy, mock_state_machine, mock_transcribe):
        """Test fallback strategy for long text"""
        with patch('macdictate.core.typer.FastTyper.type_text') as mock_type_text, \
             patch('macdictate.core.clipboard.ClipboardManager') as mock_clipboard, \
             patch('macdictate.core.recorder.Quartz') as mock_quartz:
             
             # Create long text > 1000 chars
             long_text = "A" * 1005
             mock_transcribe.return_value = {"text": long_text}
             self.recorder.audio_queue.put(MagicMock())
             
             # Action
             self.recorder.transcribe_and_type(use_gemini=False)
             
             # Assert
             # FastTyper should NOT be called because check happens before
             mock_type_text.assert_not_called()
             
             # Fallback path
             mock_clipboard.snapshot.assert_called_once()
             mock_copy.assert_called_with(long_text)
             mock_clipboard.restore.assert_not_called() # Restore is async/timer based, confusing to test here without mocking timer
             
             # Verify Cmd+V posted
             mock_quartz.CGEventCreateKeyboardEvent.assert_called()
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


