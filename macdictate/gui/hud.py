import Cocoa
import objc
from PyObjCTools import AppHelper
from macdictate.core.state import state_machine, AppState

class HUDView(Cocoa.NSView):
    def initWithFrame_(self, frame):
        self = objc.super(HUDView, self).initWithFrame_(frame)
        if self:
            self.setWantsLayer_(True)
            self.layer().setMasksToBounds_(False) # Allow shadow to spill out
            
            # Application of Shadow to the Container
            self.layer().setShadowOpacity_(0.3)
            self.layer().setShadowRadius_(8.0) # Slightly loose shadow
            self.layer().setShadowOffset_((0, -3))
            self.layer().setShadowColor_(Cocoa.NSColor.blackColor().CGColor())
            
            # Visual Effect Subview (The Glass)
            self.effect_view = Cocoa.NSVisualEffectView.alloc().initWithFrame_(self.bounds())
            self.effect_view.setAutoresizingMask_(Cocoa.NSViewWidthSizable | Cocoa.NSViewHeightSizable)
            self.effect_view.setMaterial_(Cocoa.NSVisualEffectMaterialPopover) # Lighter glass
            self.effect_view.setBlendingMode_(Cocoa.NSVisualEffectBlendingModeBehindWindow)
            self.effect_view.setState_(Cocoa.NSVisualEffectStateActive)
            
            self.effect_view.setWantsLayer_(True)
            self.effect_view.layer().setCornerRadius_(12.0)
            self.effect_view.layer().setMasksToBounds_(True) # Clip content to corners
            
            # Border on the Effect View
            self.effect_view.layer().setBorderWidth_(1.5)
            self.effect_view.layer().setBorderColor_(Cocoa.NSColor.clearColor().CGColor())
            
            self.addSubview_(self.effect_view)
            
            # Text Label (Child of Effect View? Or Sibling?)
            # Sibling is better to avoid clipping if we animate, but Child is easier for layout.
            # Child of Effect View ensures it stays inside the glass.
            self.label = Cocoa.NSTextField.alloc().initWithFrame_(self.bounds())
            self.label.setBezeled_(False)
            self.label.setDrawsBackground_(False)
            self.label.setEditable_(False)
            self.label.setSelectable_(False)
            self.label.setAlignment_(Cocoa.NSTextAlignmentCenter)
            self.label.setFont_(Cocoa.NSFont.systemFontOfSize_weight_(15.0, Cocoa.NSFontWeightMedium))
            self.label.setTextColor_(Cocoa.NSColor.labelColor()) # Adaptive color
            self.label.setStringValue_("Idle")
            
            self.effect_view.addSubview_(self.label)
            
            self.updateLabelFrame()
            
        return self

    def updateLabelFrame(self):
        # Center the label vertically and horizontally
        bounds = self.bounds()
        h = 24 
        y = (bounds.size.height - h) / 2.0 - 1
        self.label.setFrame_(Cocoa.NSMakeRect(0, y, bounds.size.width, h))

    def setStatus_message_(self, state, message):
        self.label.setStringValue_(message)
        
        # Determine Color
        color = None
        if state == AppState.RECORDING:
            color = Cocoa.NSColor.systemRedColor()
            self.startPulse_(color)
        elif state == AppState.PROCESSING:
            color = Cocoa.NSColor.systemBlueColor()
            self.startPulse_(color)
        elif state == AppState.SUCCESS:
            color = Cocoa.NSColor.systemGreenColor()
            self.stopPulse()
            self.effect_view.layer().setBorderColor_(color.CGColor())
        elif state == AppState.ERROR:
            color = Cocoa.NSColor.systemRedColor()
            self.stopPulse()
            self.effect_view.layer().setBorderColor_(color.CGColor())
        else:
            self.stopPulse()
            self.effect_view.layer().setBorderColor_(Cocoa.NSColor.clearColor().CGColor())

    def startPulse_(self, ns_color):
        color = ns_color.CGColor()
        self.effect_view.layer().setBorderColor_(color)
        
        anim = Cocoa.CABasicAnimation.animationWithKeyPath_("borderColor")
        anim.setFromValue_(color)
        color_faded = ns_color.colorWithAlphaComponent_(0.3).CGColor()
        anim.setToValue_(color_faded)
        anim.setDuration_(0.8)
        anim.setAutoreverses_(True)
        anim.setRepeatCount_(float("inf"))
        
        self.effect_view.layer().addAnimation_forKey_(anim, "pulse")

    def stopPulse(self):
        self.effect_view.layer().removeAnimationForKey_("pulse")

class HUDController(Cocoa.NSObject):
    def init(self):
        self = objc.super(HUDController, self).init()
        if self:
            # Create Window - Compact
            w = 180
            h = 44
            rect = Cocoa.NSMakeRect(0, 0, w, h)
            
            style_mask = Cocoa.NSWindowStyleMaskBorderless | Cocoa.NSWindowStyleMaskNonactivatingPanel
            self.window = Cocoa.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                rect, style_mask, Cocoa.NSBackingStoreBuffered, False
            )
            
            self.window.setLevel_(Cocoa.NSScreenSaverWindowLevel)
            self.window.setBackgroundColor_(Cocoa.NSColor.clearColor())
            self.window.setOpaque_(False) 
            self.window.setHasShadow_(False) # Disable native window shadow (we draw our own)
            self.window.setIgnoresMouseEvents_(True)
            self.window.setFloatingPanel_(True)
            
            # Position - Bottom Area
            # screen_frame = Cocoa.NSScreen.mainScreen().frame()
            screen = Cocoa.NSScreen.mainScreen()
            visible_frame = screen.visibleFrame() # Respects Dock/Menu Bar
            
            cx = visible_frame.origin.x + (visible_frame.size.width - w) / 2
            # Position approx 100px above the dock (or bottom of visible area)
            cy = visible_frame.origin.y + 100
             
            self.window.setFrameOrigin_((cx, cy))
            
            # Set Content View
            self.view = HUDView.alloc().initWithFrame_(rect)
            self.window.setContentView_(self.view)
            
            # Subscribe
            state_machine.add_observer(self.on_state_change)
            
            # Initially Hide
            self.window.setAlphaValue_(0.0)
            self.window.orderOut_(None)
            
        return self

    def on_state_change(self, state, data):
        AppHelper.callAfter(self._update_ui, state, data)

    def _update_ui(self, state, data):
        if state == AppState.IDLE:
            # Fade Out
            Cocoa.NSAnimationContext.beginGrouping()
            Cocoa.NSAnimationContext.currentContext().setDuration_(0.3)
            self.window.animator().setAlphaValue_(0.0)
            Cocoa.NSAnimationContext.endGrouping()
        else:
            msg = ""
            if state == AppState.RECORDING:
                msg = "Listening..."
            elif state == AppState.PROCESSING:
                msg = "Processing..."
                if data.get('use_gemini'):
                    msg = "✨ Magic..." 
            elif state == AppState.SUCCESS:
                msg = "Copied!"
            elif state == AppState.ERROR:
                msg = data.get('error', "Error!")
            
            self.view.setStatus_message_(state, msg)
            
            # Fade In
            self.window.orderFront_(None)
            Cocoa.NSAnimationContext.beginGrouping()
            Cocoa.NSAnimationContext.currentContext().setDuration_(0.15)
            self.window.animator().setAlphaValue_(1.0)
            Cocoa.NSAnimationContext.endGrouping()
