import unittest
from unittest.mock import MagicMock, patch, call
import sys
from pathlib import Path

# Add project root to path to allow importing modules
sys.path.append(str(Path(__file__).parent.parent))

from zerog.core.typer import FastTyper
from zerog.core.clipboard import ClipboardManager

class TestFastTyper(unittest.TestCase):
    
    @patch('zerog.core.typer.Quartz')
    @patch('zerog.core.typer.time')
    def test_type_text_chunking(self, mock_time, mock_quartz):
        """Test that text is split into correct chunks and events are posted."""
        # Setup
        text = "Hello World" # 11 chars
        chunk_size = 5
        
        # Action
        result = FastTyper.type_text(text, chunk_size=chunk_size, delay=0.01)
        
        # Assert
        self.assertTrue(result)
        
        # Should have 3 chunks: "Hello" (5), " Worl" (5), "d" (1)
        self.assertEqual(mock_quartz.CGEventKeyboardSetUnicodeString.call_count, 3)
        
        # Total events: 11 (sweep) + 3 chunks * 2 (Down/Up) = 17
        self.assertEqual(mock_quartz.CGEventPost.call_count, 17)
        
        # Verify calls
        calls = mock_quartz.CGEventKeyboardSetUnicodeString.call_args_list
        self.assertEqual(calls[0][0][2], "Hello")
        self.assertEqual(calls[1][0][2], " Worl")
        self.assertEqual(calls[2][0][2], "d")
        
        # Verify delay was called
        # Depending on loop implementation, time.sleep might differ, but at least ensure it was called
        self.assertTrue(mock_time.sleep.called)

    @patch('zerog.core.typer.Quartz')
    def test_type_empty_string(self, mock_quartz):
        """Test that empty string does nothing."""
        result = FastTyper.type_text("")
        self.assertTrue(result)
        mock_quartz.CGEventPost.assert_not_called()

    @patch('zerog.core.typer.Quartz')
    def test_failure_handling(self, mock_quartz):
        """Test that exceptions return False."""
        mock_quartz.CGEventCreateKeyboardEvent.side_effect = Exception("Quartz Failure")
        result = FastTyper.type_text("Test")
        self.assertFalse(result)


class TestClipboardManager(unittest.TestCase):
    
    @patch('zerog.core.clipboard.Cocoa')
    def test_snapshot_empty(self, mock_cocoa):
        """Test snapshot on empty clipboard."""
        pb_mock = MagicMock()
        pb_mock.pasteboardItems.return_value = []
        mock_cocoa.NSPasteboard.generalPasteboard.return_value = pb_mock
        
        result = ClipboardManager.snapshot()
        self.assertEqual(result, [])

    @patch('zerog.core.clipboard.Cocoa')
    def test_snapshot_capture(self, mock_cocoa):
        """Test capturing a snapshot with items."""
        # Mock NSPasteboard and its items
        pb_mock = MagicMock()
        mock_cocoa.NSPasteboard.generalPasteboard.return_value = pb_mock
        
        item_mock = MagicMock()
        item_mock.types.return_value = ["public.utf8-plain-text", "public.html"]
        item_mock.dataForType_.side_effect = lambda t: f"data_{t}"
        
        pb_mock.pasteboardItems.return_value = [item_mock]
        
        # Action
        snapshot = ClipboardManager.snapshot()
        
        # Assert
        self.assertEqual(len(snapshot), 1)
        self.assertEqual(snapshot[0]["public.utf8-plain-text"], "data_public.utf8-plain-text")
        self.assertEqual(snapshot[0]["public.html"], "data_public.html")

    @patch('zerog.core.clipboard.Cocoa')
    def test_restore(self, mock_cocoa):
        """Test restoring from snapshot."""
        # Setup snapshot data
        snapshot = [{"public.utf8-plain-text": "restored_data"}]
        
        pb_mock = MagicMock()
        mock_cocoa.NSPasteboard.generalPasteboard.return_value = pb_mock
        
        # Mock Item alloc/init
        item_mock = MagicMock()
        mock_cocoa.NSPasteboardItem.alloc.return_value.init.return_value = item_mock
        
        # Action
        ClipboardManager.restore(snapshot)
        
        # Assert
        pb_mock.clearContents.assert_called_once()
        item_mock.setData_forType_.assert_called_with("restored_data", "public.utf8-plain-text")
        pb_mock.writeObjects_.assert_called_with([item_mock])

if __name__ == '__main__':
    unittest.main()
