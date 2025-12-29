import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macdictate.core import gemini

class TestGeminiProcessor(unittest.TestCase):

    @patch('macdictate.core.gemini.model')
    def test_process_text_success(self, mock_model):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "Polished text"
        mock_model.generate_content.return_value = mock_response
        
        result = gemini.process_text("Raw text")
        self.assertEqual(result, "Polished text")
        mock_model.generate_content.assert_called_once_with("Text: Raw text")

    def test_process_text_empty_input(self):
        result = gemini.process_text("")
        self.assertEqual(result, "")
        
        result = gemini.process_text("   ")
        self.assertEqual(result, "   ")

    def test_process_text_no_model(self):
        # Test when model is None
        # Use patch.object because 'gemini' is now a module object
        with patch.object(gemini, 'model', None):
            result = gemini.process_text("Raw text")
            self.assertEqual(result, "Raw text")

    @patch('macdictate.core.gemini.model')
    def test_process_text_exception(self, mock_model):
        # Mock exception during API call
        mock_model.generate_content.side_effect = Exception("API Error")
        
        result = gemini.process_text("Raw text")
        self.assertEqual(result, "Raw text")

if __name__ == '__main__':
    unittest.main()
