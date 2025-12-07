import os
import logging
import google.generativeai as genai

# Setup logger for this module
logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model_name = "gemini-1.5-flash"
        self.model = None

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                logger.info(f"AIProcessor initialized with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to configure Gemini in AIProcessor: {e}", exc_info=True)
        else:
            logger.warning("GOOGLE_API_KEY not found. AI processing will be disabled.")

    def process_text(self, text):
        """
        Post-processes the transcribed text using Gemini to improve formatting.
        Returns the original text if processing fails or model is unavailable.
        """
        if not self.model:
            return text

        try:
            prompt = (
                "You are a helpful assistant that lightly edits transcribed speech. "
                "Your only job is to add necessary punctuation, break text into paragraphs, "
                "and format lists if the speaker is clearly listing items. "
                "Do not change the words, tone, or meaning. "
                "Output only the edited text.\n\n"
                f"Transcript: {text}"
            )
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"AI processing failed: {e}", exc_info=True)
            return text
