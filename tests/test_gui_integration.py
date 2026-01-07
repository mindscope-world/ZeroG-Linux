import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Scoped Shim Classes
class ShimWKWebView:
    """Simulate WKWebView base class behavior"""
    @classmethod
    def alloc(cls):
        return cls()

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
    NSPanel = MagicMock()
    
    class NSObject:
        def init(self):
            return self
            
        @classmethod
        def alloc(cls):
            return cls()
            
    NSApp = MagicMock()
    NSEvent = MagicMock()
    NSScreen = MagicMock()
    NSPointInRect = MagicMock()
    
    # Simple Geometry Mocks
    class _NSPoint:
        def __init__(self, x, y): self.x=x; self.y=y
    class _NSSize:
        def __init__(self, w, h): self.width=w; self.height=h
    class _NSRect:
        def __init__(self, o, s): self.origin=o; self.size=s
    
    @staticmethod
    def NSMakeRect(x, y, w, h):
        return ShimCocoa._NSRect(ShimCocoa._NSPoint(x, y), ShimCocoa._NSSize(w, h))

    @staticmethod
    def NSPoint(x, y):
        return ShimCocoa._NSPoint(x, y)
        
    # Constants
    NSWindowStyleMaskBorderless = 0
    NSWindowStyleMaskNonactivatingPanel = 0
    NSBackingStoreBuffered = 0
    NSScreenSaverWindowLevel = 0
    NSWindowCollectionBehaviorCanJoinAllSpaces = 0
    NSWindowCollectionBehaviorStationary = 0
    NSWindowCollectionBehaviorIgnoresCycle = 0
    
    # Contexts
    NSAnimationContext = MagicMock()

class ShimObjC:
    class SuperProxy:
        def __init__(self, obj): self.obj = obj
        def init(self): return self.obj
        def initWithFrame_configuration_(self, f, c): return self.obj
        def __getattr__(self, name): return lambda *args: self.obj
        
    @staticmethod
    def super(cls_type, obj):
        return ShimObjC.SuperProxy(obj)

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
        if 'zerog.gui.hud' in sys.modules:
            del sys.modules['zerog.gui.hud']

    def tearDown(self):
        self.modules_patcher.stop()

    def test_hud_controller_audio_update(self):
        from zerog.gui.hud import HUDView
        
        # Instantiate directly using Shim base
        view = HUDView()
        
        # Manually mock evaluate_js locally to intercept calls
        view.evaluate_js = MagicMock()
        
        # Test Case 1: NOT ready (should not call)
        view.is_js_ready = False
        view.updateAudioLevel_(0.1)
        view.evaluate_js.assert_not_called()
        
        # Test Case 2: Broadcating when ready
        view.is_js_ready = True
        view.updateAudioLevel_(0.1) # 0.1 * 5 = 0.5
        view.evaluate_js.assert_called_with("window.applyShadow(0.50)")
        
        view.updateAudioLevel_(0.5) # 0.5 * 5 = 2.5 -> clamped to 1.0
        view.evaluate_js.assert_called_with("window.applyShadow(1.00)")

    def test_stop_button_interception(self):
        from zerog.gui.hud import HUDView
        
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


    def test_hud_update_position(self):
        from zerog.gui.hud import HUDController
        Cocoa = self.mock_cocoa
        
        # Mock dependencies
        mock_screen1 = MagicMock()
        mock_screen1.frame.return_value = Cocoa.NSMakeRect(0, 0, 1920, 1080)
        mock_screen1.visibleFrame.return_value = Cocoa.NSMakeRect(0, 50, 1920, 1030)
        mock_screen1.localizedName.return_value = "Screen 1"
        
        mock_screen2 = MagicMock()
        mock_screen2.frame.return_value = Cocoa.NSMakeRect(1920, 0, 1920, 1080)
        mock_screen2.visibleFrame.return_value = Cocoa.NSMakeRect(1920, 50, 1920, 1030)
        mock_screen2.localizedName.return_value = "Screen 2"
        
        self.mock_cocoa.NSScreen.screens.return_value = [mock_screen1, mock_screen2]
        
        # Instantiate controller
        controller = HUDController.alloc().init()
        
        # Test Case 1: Mouse on Screen 1
        self.mock_cocoa.NSEvent.mouseLocation.return_value = Cocoa.NSPoint(500, 500)
        # Helper for NSPointInRect
        def side_effect_point_in_rect(point, rect):
            # Simple check if point is in rect
            return (point.x >= rect.origin.x and point.x < rect.origin.x + rect.size.width and
                    point.y >= rect.origin.y and point.y < rect.origin.y + rect.size.height)
            
        self.mock_cocoa.NSPointInRect.side_effect = side_effect_point_in_rect
        
        controller.update_position()
        
        # Screen 1 width 1920, HUD width 525 -> center x = 0 + (1920-525)/2 = 697.5
        expected_x1 = 0 + (1920 - 525) / 2
        self.assertEqual(controller.centerX, expected_x1)
        
        # Test Case 2: Mouse on Screen 2
        self.mock_cocoa.NSEvent.mouseLocation.return_value = Cocoa.NSPoint(2500, 500)
        controller.update_position()
        
        # Screen 2 x=1920, width 1920 -> center x = 1920 + (1920-525)/2 = 1920 + 697.5 = 2617.5
        expected_x2 = 1920 + (1920 - 525) / 2
        self.assertEqual(controller.centerX, expected_x2)


if __name__ == '__main__':
    unittest.main()
