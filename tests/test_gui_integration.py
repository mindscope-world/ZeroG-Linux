import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Scoped Shim Classes
class ShimWKWebView:
    """Simulate WKWebView base class behavior"""
    def initWithFrame_configuration_(self, frame, config):
        return self
        
    def setWantsLayer_(self, val): pass
    def setValue_forKey_(self, val, key): pass
    def setUnderPageBackgroundColor_(self, color): pass
    def loadHTMLString_baseURL_(self, html, url): pass
    def setNavigationDelegate_(self, delegate): pass
    def evaluateJavaScript_completionHandler_(self, script, handler): pass

class ShimCocoa:
    NSColor = MagicMock()
    NSPanel = MagicMock()
    NSObject = object # HUDController inherits NSObject
    NSApp = MagicMock()

class ShimObjC:
    def super(cls, self):
        return self # Simple pass-through for super() calls in tests

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestHUDIntegration(unittest.TestCase):
    def setUp(self):
        # Create Mocks with Shims
        self.mock_webkit = MagicMock()
        self.mock_webkit.WKWebView = ShimWKWebView
        self.mock_webkit.WKWebViewConfiguration = MagicMock()
        self.mock_webkit.WKNavigationActionPolicyCancel = 0
        self.mock_webkit.WKNavigationActionPolicyAllow = 1
        
        self.mock_objc = MagicMock()
        self.mock_objc.super = ShimObjC().super
        
        self.mock_cocoa = ShimCocoa()
        
        # Patch modules safely using patch.dict
        self.modules_patcher = patch.dict(sys.modules, {
            'objc': self.mock_objc,
            'Cocoa': self.mock_cocoa,
            'Quartz': MagicMock(),
            'WebKit': self.mock_webkit,
            'AppKit': MagicMock(),
            'Foundation': MagicMock(),
            'CoreFoundation': MagicMock(),
            'PyObjCTools': MagicMock(),
            'PyObjCTools.AppHelper': MagicMock(),
        })
        self.modules_patcher.start()
        
        # Reloading HUD module to apply shims
        if 'macdictate.gui.hud' in sys.modules:
            del sys.modules['macdictate.gui.hud']

    def tearDown(self):
        self.modules_patcher.stop()

    def test_hud_controller_audio_update(self):
        from macdictate.gui.hud import HUDView
        
        # Instantiate directly using Shim base
        # Logic: HUDView.initWithFrame_(None) -> super().initWithFrame_configuration_ -> returns self
        view = HUDView()
        # Manually call init logic if needed, but the class logic calls super()...
        # Wait, python instantiation HUDView() doesn't call initWithFrame_ automatically. 
        # But we are testing updateAudioLevel_, which depends on 'evaluate_js'.
        
        # Manually mock evaluate_js locally to intercept calls
        view.evaluate_js = MagicMock()
        
        # Test audio update broadcasting
        view.updateAudioLevel_(0.1) # 0.1 * 5 = 0.5
        view.evaluate_js.assert_called_with("window.applyShadow(0.50)")
        
        view.updateAudioLevel_(0.5) # 0.5 * 5 = 2.5 -> clamped to 1.0
        view.evaluate_js.assert_called_with("window.applyShadow(1.00)")

    def test_stop_button_interception(self):
        from macdictate.gui.hud import HUDView
        
        view = HUDView()
        
        # Mock navigation action
        mock_nav = MagicMock()
        mock_nav.request().URL().absoluteString.return_value = "app://stopRecording"
        
        mock_handler = MagicMock()
        
        # Setup Delegate mock on the ShimCocoa.NSApp
        mock_delegate = MagicMock()
        self.mock_cocoa.NSApp.delegate.return_value = mock_delegate
        
        view.webView_decidePolicyForNavigationAction_decisionHandler_(
            None, mock_nav, mock_handler
        )
        
        # Verify stop recording called
        mock_delegate.recorder.stop_recording.assert_called_once()
        
        # Verify navigation cancelled
        mock_handler.assert_called_with(0) # PolicyCancel = 0

if __name__ == '__main__':
    unittest.main()
