import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging

# Load environment variables (like our API key) from the .env file
load_dotenv()

# Setup logging for this specific file
logger = logging.getLogger(__name__)

# The specific Google Gemini model we are using for text cleanup.
# IMPORTANT: This feature sends text to Google's servers for processing.
MODEL_NAME = "gemini-2.0-flash-exp" # Updated to faster flash model

# --- Gemini API Initialization ---
# Get the API key from our environment
api_key = os.getenv("GOOGLE_API_KEY")

client = None
system_instruction = "Reformulate text as a professional document."
IS_CONFIGURED = False

if api_key:
    try:
        # Initialize the new Google GenAI client
        client = genai.Client(api_key=api_key)
        
        # Load the specific instructions for Gemini
        # prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_prompt.txt")
        # This finds the directory where THIS file lives, then looks for the prompt
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(BASE_DIR, "gemini_prompt.txt")
        
        if os.path.exists(prompt_path):
            with open(prompt_path, "r") as f:
                system_instruction = f.read().strip()
        
        # --- Model Warmup ---
        def warmup_gemini():
            try:
                client.models.generate_content(
                    model=MODEL_NAME,
                    contents="Warmup.",
                    config=types.GenerateContentConfig(
                        max_output_tokens=10,
                    )
                )
                logger.info("Gemini Warmup Complete.")
            except Exception as e:
                logger.debug(f"Gemini Warmup failed (ignoring): {e}")

        import threading
        threading.Thread(target=warmup_gemini, daemon=True).start()
        
        IS_CONFIGURED = True
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
else:
    logger.warning("GOOGLE_API_KEY not found in environment variables. Gemini processing will be skipped.")

def process_text(text):
    """
    Takes raw transcription text and sends it to Gemini for polishing.
    Returns the polished text, or the original text if processing fails.
    """
    if not client or not text.strip():
        return text

    try:
        # Configuration for how Gemini generates text
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0,
            max_output_tokens=4096,
            response_mime_type="text/plain",
        )
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"Text: {text}",
            config=config
        )
        
        if response and response.text:
            processed = response.text.strip()
            logger.info(f"Gemini successfully processed transcription: '{processed}'")
            return processed
        return text
    except Exception as e:
        logger.error(f"Gemini processing failed: {e}")
        return text
