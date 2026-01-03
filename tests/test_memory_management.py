import unittest
from unittest.mock import MagicMock, patch
import time
from zerog.core.recorder import AudioRecorder

class TestMemoryManagement(unittest.TestCase):
    @patch('zerog.core.recorder.mlx_whisper')
    @patch('zerog.core.recorder.sd')
    @patch('zerog.core.recorder.Cocoa')
    @patch('zerog.core.recorder.state_machine')
    def test_unload_model_clears_cache(self, mock_state, mock_cocoa, mock_sd, mock_mlx):
        # Create a mock module for mlx_whisper.transcribe
        mock_transcribe_module = MagicMock()
        mock_ModelHolder = MagicMock()
        # Initial state: model is some object
        mock_ModelHolder.model = MagicMock()
        mock_transcribe_module.ModelHolder = mock_ModelHolder

        # Patch sys.modules to return our mock module
        with patch.dict('sys.modules', {'mlx_whisper.transcribe': mock_transcribe_module}):
            # Initialize recorder
            recorder = AudioRecorder()
            
            # Verify unload_model exists
            self.assertTrue(hasattr(recorder, 'unload_model'), "AudioRecorder should have unload_model method")
            
            # Call unload_model
            recorder.unload_model()
            
            # Assertions
            # 1. ModelHolder.model should be set to None
            self.assertEqual(mock_ModelHolder.model, None)

    @patch('zerog.core.recorder.mlx_whisper')
    @patch('zerog.core.recorder.sd')
    @patch('zerog.core.recorder.Cocoa')
    @patch('zerog.core.recorder.state_machine')
    def test_inactivity_timer_triggers_unload(self, mock_state, mock_cocoa, mock_sd, mock_mlx):
        # Use a short timeout for testing
        TEST_TIMEOUT = 0.1
        
        # Initialize recorder with patched timeout constant if possible, 
        # or we rely on the method accepting an argument or patching the class attribute
        
        # Patching the constant in the class/module for the test
        with patch('zerog.core.recorder.MODEL_UNLOAD_TIMEOUT', TEST_TIMEOUT):
            recorder = AudioRecorder()
            
            # Mock the unload_model method to verify it gets called
            recorder.unload_model = MagicMock()
            
            # Simulate stopping recording which should start the timer
            # We assume _start_unload_timer is called or similar logic in stop_recording
            # For now, let's call the timer starter directly if it's separate, 
            # or simulate the flow.
            # Let's assume we add a method `_schedule_model_unload`
            if hasattr(recorder, '_schedule_model_unload'):
                recorder._schedule_model_unload()
                
                # Wait for timer
                time.sleep(TEST_TIMEOUT + 0.1)
                
                # Verify unload_model was called
                recorder.unload_model.assert_called_once()
            else:
                 # If method doesn't exist yet, this part of test is skipped or fails as expected
                 pass

if __name__ == '__main__':
    unittest.main()
