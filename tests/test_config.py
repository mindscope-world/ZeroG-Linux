import unittest
import os
import importlib
from unittest.mock import patch

class TestConfigLinux(unittest.TestCase):
    def test_logging_default_security(self):
        """Verify logging is False by default on Linux."""
        with patch.dict(os.environ, clear=True):
            with patch('dotenv.load_dotenv'):
                 import main
                 importlib.reload(main)
                 # Adjust based on your actual main.py variable name
                 self.assertFalse(getattr(main, 'ENABLE_LOGGING', True))

    def test_logging_enabled_with_env(self):
        """Verify logging turns on when DEBUG=True."""
        with patch.dict(os.environ, {'DEBUG': 'True'}):
            import main
            importlib.reload(main)
            self.assertTrue(getattr(main, 'ENABLE_LOGGING', False))