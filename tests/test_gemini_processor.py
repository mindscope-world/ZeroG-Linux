import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add the project root to sys.path to allow importing gemini_processor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gemini_processor

class TestGeminiProcessor(unittest.TestCase):

    @patch('gemini_processor.model')
    def test_process_text_success(self, mock_model):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "Polished text"
        mock_model.generate_content.return_value = mock_response
        
        result = gemini_processor.process_text("Raw text")
        self.assertEqual(result, "Polished text")
        mock_model.generate_content.assert_called_once_with("Text: Raw text")

    def test_process_text_empty_input(self):
        result = gemini_processor.process_text("")
        self.assertEqual(result, "")
        
        result = gemini_processor.process_text("   ")
        self.assertEqual(result, "   ")

    @patch('gemini_processor.model')
    def test_process_text_no_model(self, mock_model):
        # Test when model is None
        with patch('gemini_processor.model', None):
            result = gemini_processor.process_text("Raw text")
            self.assertEqual(result, "Raw text")

    @patch('gemini_processor.model')
    def test_process_text_exception(self, mock_model):
        # Mock exception during API call
        mock_model.generate_content.side_effect = Exception("API Error")
        
        result = gemini_processor.process_text("Raw text")
        self.assertEqual(result, "Raw text")

if __name__ == '__main__':
    unittest.main()
