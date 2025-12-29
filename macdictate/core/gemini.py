import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# Load environment variables (like our API key) from the .env file
load_dotenv()

# Setup logging for this specific file
logger = logging.getLogger(__name__)

# The specific Google Gemini model we are using for text cleanup.
# IMPORTANT: This feature sends text to Google's servers for processing.
MODEL_NAME = "gemini-3-flash-preview"

# --- Gemini API Initialization ---
# Get the API key from our environment
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    # If a key exists, configure the Google AI library
    genai.configure(api_key=api_key)
    
    # Load the specific instructions for Gemini
    # We look for the file in the same directory as this script (macdictate/core)
    prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_prompt.txt")
    
    # If not found there (e.g. frozen with different layout), check Resources? 
    # For now, py2app data_files putting it in core/ should work with above.
    
    try:
        with open(prompt_path, "r") as f:
            system_instruction = f.read().strip()
    except Exception as e:
        # If the file is missing, use a simple default instruction
        logger.error(f"Failed to load gemini_prompt.txt: {e}")
        system_instruction = "Reformulate text as a professional document."
    
    # Configuration for how Gemini generates text
    generation_config = {
        "temperature": 0.0, # 0.0 means "be predictable and stay on task", 1.0 would be "be creative"
        "max_output_tokens": 4096,
        "response_mime_type": "text/plain",
    }
    
    # Create the model object that we will use to process text
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_instruction,
        generation_config=generation_config
    )
    
    # --- Model Warmup ---
    # Like Whisper, Gemini can be slow on the very first request.
    # We send a tiny request now so it's "awake" when the user needs it.
    def warmup_gemini():
        try:
            model.generate_content("Warmup.")
            logger.info("Gemini Warmup Complete.")
        except Exception as e:
            # If warmup fails (maybe no internet), we just ignore it for now
            logger.debug(f"Gemini Warmup failed (ignoring): {e}")

    # Run the warmup in the background so it doesn't slow down the main app startup
    import threading
    threading.Thread(target=warmup_gemini, daemon=True).start()
    
    # Flag to tell the rest of the app that Gemini is ready to use
    IS_CONFIGURED = True
else:
    # If no API key is found, we can't use Gemini
    logger.warning("GOOGLE_API_KEY not found in environment variables. Gemini processing will be skipped.")
    model = None
    IS_CONFIGURED = False

def process_text(text):
    """
    Takes raw transcription text and sends it to Gemini for polishing.
    Returns the polished text, or the original text if processing fails.
    """
    if not model or not text.strip():
        # If Gemini isn't set up or text is empty, just return what we have
        return text

    # We send the text to Gemini with a simple label
    prompt = f"Text: {text}"

    try:
        # Send the request to Google's servers
        response = model.generate_content(prompt)
        if response and response.text:
            processed = response.text.strip()
            logger.info("Gemini successfully processed transcription.")
            return processed
        return text
    except Exception as e:
        # If something goes wrong (internet outage, API error), fall back to original text
        logger.error(f"Gemini processing failed: {e}")
        return text
