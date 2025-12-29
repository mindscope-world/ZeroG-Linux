import Cocoa
import objc
from PyObjCTools import AppHelper
from macdictate.core.state import state_machine, AppState

class HUDView(Cocoa.NSView):
    def initWithFrame_(self, frame):
        self = objc.super(HUDView, self).initWithFrame_(frame)
        if self:
            self.text = "Idle"
            self.bg_color = Cocoa.NSColor.colorWithWhite_alpha_(0.1, 0.8) # Dark semi-transparent
        return self

    def setStatus_message_(self, state, message):
        self.text = message
        if state == AppState.RECORDING:
            self.bg_color = Cocoa.NSColor.systemRedColor().colorWithAlphaComponent_(0.9)
        elif state == AppState.PROCESSING:
            self.bg_color = Cocoa.NSColor.systemBlueColor().colorWithAlphaComponent_(0.9)
        else:
            self.bg_color = Cocoa.NSColor.blackColor().colorWithAlphaComponent_(0.7)
        
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        # Draw Rounded Background
        path = Cocoa.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(self.bounds(), 12.0, 12.0)
        self.bg_color.setFill()
        path.fill()
        
        # Draw Text
        text_str = self.text
        attrs = {
            Cocoa.NSFontAttributeName: Cocoa.NSFont.systemFontOfSize_weight_(18.0, Cocoa.NSFontWeightMedium),
            Cocoa.NSForegroundColorAttributeName: Cocoa.NSColor.whiteColor()
        }
        
        ns_str = Cocoa.NSString.stringWithString_(text_str)
        size = ns_str.sizeWithAttributes_(attrs)
        
        x = (self.bounds().size.width - size.width) / 2.0
        y = (self.bounds().size.height - size.height) / 2.0
        
        ns_str.drawAtPoint_withAttributes_((x, y), attrs)

class HUDController(Cocoa.NSObject):
    def init(self):
        self = objc.super(HUDController, self).init()
        if self:
            # Create Window
            w = 200
            h = 60
            rect = Cocoa.NSMakeRect(0, 0, w, h)
            
            style_mask = Cocoa.NSWindowStyleMaskBorderless | Cocoa.NSWindowStyleMaskNonactivatingPanel
            self.window = Cocoa.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                rect, style_mask, Cocoa.NSBackingStoreBuffered, False
            )
            
            self.window.setLevel_(Cocoa.NSScreenSaverWindowLevel)
            self.window.setBackgroundColor_(Cocoa.NSColor.clearColor())
            self.window.setOpaque_(False)
            self.window.setIgnoresMouseEvents_(True)
            self.window.setFloatingPanel_(True)
            
            # Center on screen initially (or we can track mouse)
            # For now, center on main screen
            screen_frame = Cocoa.NSScreen.mainScreen().frame()
            cx = screen_frame.origin.x + (screen_frame.size.width - w) / 2
            cy = screen_frame.origin.y + (screen_frame.size.height - h) / 4 # Bottom third roughly
            self.window.setFrameOrigin_((cx, cy))
            
            # Set Content View
            self.view = HUDView.alloc().initWithFrame_(rect)
            self.window.setContentView_(self.view)
            
            # Subscribe
            state_machine.add_observer(self.on_state_change)
            
            # Initially Hide
            self.window.orderOut_(None)
            
        return self

    def on_state_change(self, state, data):
        AppHelper.callAfter(self._update_ui, state, data)

    def _update_ui(self, state, data):
        if state == AppState.IDLE:
            self.window.orderOut_(None) # Hide
        else:
            msg = ""
            if state == AppState.RECORDING:
                msg = "Listening..."
            elif state == AppState.PROCESSING:
                msg = "Processing..."
                if data.get('use_gemini'):
                    msg = "Polishing w/ Gemini..."
            elif state == AppState.SUCCESS:
                msg = "Copied!"
            elif state == AppState.ERROR:
                msg = "Error!"
            
            self.view.setStatus_message_(state, msg)
            self.window.orderFront_(None) # Show
            
            if state == AppState.SUCCESS or state == AppState.ERROR:
                pass # The Recorder handles the reset to IDLE, which will hide this.
