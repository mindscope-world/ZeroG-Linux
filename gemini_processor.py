import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Options: "gemini-3-flash-preview", "gemini-1.5-flash"
MODEL_NAME = "gemini-3-flash-preview"

# Initialize Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    
    # Optimization: Load system_instruction from external file for easier iteration
    prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_prompt.txt")
    try:
        with open(prompt_path, "r") as f:
            system_instruction = f.read().strip()
    except Exception as e:
        logger.error(f"Failed to load gemini_prompt.txt: {e}")
        system_instruction = "Reformulate text as a professional document."
    
    generation_config = {
        "temperature": 0.0,
        "max_output_tokens": 1024,
        "response_mime_type": "text/plain",
    }
    
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_instruction,
        generation_config=generation_config
    )
    
    # --- WARMUP ---
    def warmup_gemini():
        try:
            # Simple, short prompt to trigger connection establishment and internal caching
            model.generate_content("Warmup.")
            logger.info("Gemini Warmup Complete.")
        except Exception as e:
            logger.debug(f"Gemini Warmup failed (ignoring): {e}")

    # Run warmup in a separate thread so it doesn't block main app startup
    import threading
    threading.Thread(target=warmup_gemini, daemon=True).start()
else:
    logger.warning("GOOGLE_API_KEY not found in environment variables. Gemini processing will be skipped.")
    model = None

def process_text(text):
    """
    Process transcription using Gemini for light editing and punctuation.
    """
    if not model or not text.strip():
        return text

    # Prompt is now very short since instructions are in system_instruction
    prompt = f"Text: {text}"

    try:
        response = model.generate_content(prompt)
        if response and response.text:
            processed = response.text.strip()
            logger.info("Gemini successfully processed transcription.")
            return processed
        return text
    except Exception as e:
        logger.error(f"Gemini processing failed: {e}")
        return text
