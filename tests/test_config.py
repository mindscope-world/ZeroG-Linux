import unittest
import os
import importlib
from unittest.mock import patch

class TestConfig(unittest.TestCase):
    def test_logging_default_security(self):
        """
        Verify that if DEBUG is not set in the environment,
        logging is disabled by default. 
        This ensures production/repo builds are silent/secure.
        """
        # We must prevent load_dotenv from reading the local .env file
        # AND verify that without that file (or env var), it defaults to False.
        with patch.dict(os.environ, clear=True):
            # Also patch load_dotenv to do nothing
            with patch('dotenv.load_dotenv'):
                 if 'DEBUG' in os.environ:
                     del os.environ['DEBUG']
                 
                 import main
                 importlib.reload(main)
                 
                 self.assertFalse(main.ENABLE_LOGGING, "Logging must be disabled if DEBUG env var is missing.")

    def test_logging_enabled_with_env(self):
        """
        Verify logging turns on when DEBUG=True.
        """
        with patch.dict(os.environ, {'DEBUG': 'True'}):
            import main
            importlib.reload(main)
            self.assertTrue(main.ENABLE_LOGGING)
