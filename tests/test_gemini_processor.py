import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zerog.core import gemini

class TestGeminiProcessor(unittest.TestCase):

    @patch('zerog.core.gemini.client')
    def test_process_text_success(self, mock_client):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "Polished text"
        mock_client.models.generate_content.return_value = mock_response
        
        result = gemini.process_text("Raw text")
        self.assertEqual(result, "Polished text")
        # Check call args - the new SDK uses model and contents
        args, kwargs = mock_client.models.generate_content.call_args
        self.assertEqual(kwargs['contents'], "Text: Raw text")

    def test_process_text_empty_input(self):
        result = gemini.process_text("")
        self.assertEqual(result, "")
        
        result = gemini.process_text("   ")
        self.assertEqual(result, "   ")

    def test_process_text_no_client(self):
        # Test when client is None
        with patch.object(gemini, 'client', None):
            result = gemini.process_text("Raw text")
            self.assertEqual(result, "Raw text")

    @patch('zerog.core.gemini.client')
    def test_process_text_exception(self, mock_client):
        # Mock exception during API call
        mock_client.models.generate_content.side_effect = Exception("API Error")
        
        result = gemini.process_text("Raw text")
        self.assertEqual(result, "Raw text")

if __name__ == '__main__':
    unittest.main()
