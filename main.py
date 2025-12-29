import logging
import os
import macdictate.app

# --- Configuration ---
ENABLE_LOGGING = True

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