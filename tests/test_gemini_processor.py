import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Standardized pathing for Linux environments
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zerog.core import gemini

class TestGeminiProcessor(unittest.TestCase):

    @patch('zerog.core.gemini.client')
    def test_process_text_success(self, mock_client):
        """Verify the Gemini client correctly processes raw text into polished text."""
        # Mock successful response from Google GenAI SDK
        mock_response = MagicMock()
        mock_response.text = "Polished text"
        mock_client.models.generate_content.return_value = mock_response
        
        result = gemini.process_text("Raw text")
        self.assertEqual(result, "Polished text")
        
        # Verify the call structure matches the Google GenAI 2.0+ SDK requirements
        args, kwargs = mock_client.models.generate_content.call_args
        # New SDK standard often wraps the prompt in 'contents'
        self.assertIn("Raw text", kwargs['contents'])

    def test_process_text_empty_input(self):
        """Ensure the processor returns whitespace/empty strings as-is without API calls."""
        self.assertEqual(gemini.process_text(""), "")
        self.assertEqual(gemini.process_text("   "), "   ")

    def test_process_text_no_client(self):
        """Gracefully fallback to original text if API client fails to initialize (e.g., missing API key)."""
        with patch.object(gemini, 'client', None):
            result = gemini.process_text("Raw text")
            self.assertEqual(result, "Raw text")

    @patch('zerog.core.gemini.client')
    def test_process_text_exception(self, mock_client):
        """Ensure network errors or API quota issues don't crash the app, but return the raw text instead."""
        mock_client.models.generate_content.side_effect = Exception("API Error")
        
        result = gemini.process_text("Raw text")
        self.assertEqual(result, "Raw text")

if __name__ == '__main__':
    unittest.main()