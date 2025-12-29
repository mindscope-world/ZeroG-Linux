import unittest
import main

class TestConfig(unittest.TestCase):
    def test_logging_disabled_by_default(self):
        """
        Ensure that logging is disabled by default for production builds.
        This prevents accidental commits of debug logging enabled.
        """
        self.assertFalse(main.ENABLE_LOGGING, "Logging should be disabled (ENABLE_LOGGING=False) for committed code.")

if __name__ == '__main__':
    unittest.main()
