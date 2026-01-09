# tests/test_gui_integration.py
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Ensure QApplication exists for testing UI components
app = QApplication.instance() or QApplication(sys.argv)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zerog.core.hud import LinuxHUD
from zerog.core.state import AppState

class TestHUDIntegrationLinux(unittest.TestCase):
    def setUp(self):
        # Initialize the HUD
        self.hud = LinuxHUD()
        # Mock the browser/page to intercept JavaScript calls
        self.hud.browser.page().runJavaScript = MagicMock()

    def test_hud_visibility_on_state_change(self):
        """Verify HUD shows/hides based on ZeroG state."""
        # Test Case 1: Processing state should show HUD
        self.hud.update_ui_state(AppState.PROCESSING, {'use_gemini': False})
        self.assertTrue(self.hud.isVisible())
        
        # Test Case 2: Idle state should hide HUD
        self.hud.update_ui_state(AppState.IDLE, {})
        self.assertFalse(self.hud.isVisible())

    def test_hud_js_injection_logic(self):
        """Verify correct JavaScript is sent to the Chromium engine."""
        self.hud.show()
        
        # Test Recording State
        self.hud.update_ui_state(AppState.RECORDING, {})
        self.hud.browser.page().runJavaScript.assert_called_with(
            "window.setState('recording', 'Listening...')"
        )

        # Test Success State
        self.hud.update_ui_state(AppState.SUCCESS, {})
        self.hud.browser.page().runJavaScript.assert_called_with(
            "window.setState('success', 'Copied!')"
        )

    def test_audio_level_shadow_clamping(self):
        """Verify audio levels are boosted and clamped correctly for the CSS glow."""
        self.hud.show()
        
        # 0.1 intensity * 5 boost = 0.5 shadow
        self.hud.update_audio_level(0.1)
        self.hud.browser.page().runJavaScript.assert_called_with("window.applyShadow(0.50)")
        
        # 0.5 intensity * 5 boost = 2.5 -> should be clamped to 1.0 in your logic
        self.hud.update_audio_level(0.5)
        self.hud.browser.page().runJavaScript.assert_called_with("window.applyShadow(1.00)")

    def test_screen_centering(self):
        """Verify HUD centers itself on the primary screen available geometry."""
        self.hud.center_on_screen()
        geometry = self.hud.geometry()
        screen = QApplication.primaryScreen().availableGeometry()
        
        expected_x = (screen.width() - self.hud.width()) // 2
        self.assertEqual(geometry.x(), expected_x)

if __name__ == '__main__':
    unittest.main()