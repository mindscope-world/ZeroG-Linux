import logging
import os
import macdictate.app
from dotenv import load_dotenv
import certifi

# Fix for SSL: CERTIFICATE_VERIFY_FAILED on macOS
os.environ["SSL_CERT_FILE"] = certifi.where()

load_dotenv()

# --- Configuration ---
# Logging is enabled ONLY if DEBUG=True in .env (local)
ENABLE_LOGGING = os.getenv("DEBUG", "False").lower() in ("true", "1")

def setup_logging():
    logger = logging.getLogger()
    
    if ENABLE_LOGGING:
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mac_dictate.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        # Also print to console for dev
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        logger.addHandler(console)
    else:
        logging.basicConfig(level=logging.WARNING)

if __name__ == "__main__":
    setup_logging()
    macdictate.app.run()