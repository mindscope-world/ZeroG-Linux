import unittest
from unittest.mock import MagicMock, patch, call
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from zerog.core.typer import FastTyper, ClipboardManager

class TestFastTyperLinux(unittest.TestCase):
    
    @patch('zerog.core.typer.subprocess.run')
    @patch('zerog.core.typer.pyperclip.copy')
    @patch('zerog.core.typer.ClipboardManager.snapshot')
    def test_injection_flow(self, mock_snapshot, mock_copy, mock_run):
        """Test the Linux strategy: Snapshot -> Copy -> xdotool -> Restore."""
        mock_snapshot.return_value = "original_clipboard"
        text_to_inject = "Transmitted Text"
        
        # Action
        result = FastTyper.inject(text_to_inject)
        
        # Assert
        self.assertTrue(result)
        mock_copy.assert_called_with(text_to_inject)
        # Ensure xdotool was called to paste
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        self.assertIn("xdotool", args[0])
        self.assertIn("ctrl+v", args[0])

    @patch('zerog.core.typer.subprocess.run')
    def test_failure_handling(self, mock_run):
        """Test that if xdotool fails, we return False."""
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(1, 'xdotool')
        
        result = FastTyper.inject("Test")
        self.assertFalse(result)

class TestClipboardManagerLinux(unittest.TestCase):
    
    @patch('zerog.core.typer.pyperclip.paste')
    def test_snapshot(self, mock_paste):
        mock_paste.return_value = "hello world"
        result = ClipboardManager.snapshot()
        self.assertEqual(result, "hello world")

    @patch('zerog.core.typer.pyperclip.copy')
    def test_restore(self, mock_copy):
        ClipboardManager.restore("previous data")
        mock_copy.assert_called_with("previous data")

if __name__ == '__main__':
    unittest.main()