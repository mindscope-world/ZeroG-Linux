import Cocoa
import objc
import Quartz
import math
from PyObjCTools import AppHelper
from macdictate.core.state import state_machine, AppState


# SF Symbol names for each state
STATE_ICONS = {
    AppState.IDLE: "circle",
    AppState.RECORDING: "mic.fill",
    AppState.PROCESSING: "sparkles",
    AppState.SUCCESS: "checkmark.circle.fill",
    AppState.ERROR: "exclamationmark.triangle.fill",
}

# State-specific background tint colors (very subtle)
STATE_TINTS = {
    AppState.IDLE: (0.1, 0.1, 0.12),        # Neutral dark
    AppState.RECORDING: (0.15, 0.08, 0.08),  # Subtle red warmth
    AppState.PROCESSING: (0.08, 0.1, 0.15),  # Subtle blue tint
    AppState.SUCCESS: (0.08, 0.14, 0.10),    # Subtle green tint
    AppState.ERROR: (0.15, 0.08, 0.08),      # Subtle red warmth
}


class WaveformView(Cocoa.NSView):
    """Animated waveform visualization with vertical bars."""
    
    def initWithFrame_(self, frame):
        self = objc.super(WaveformView, self).initWithFrame_(frame)
        if self:
            self.setWantsLayer_(True)
            self.layer().setMasksToBounds_(False)
            
            # Create 5 waveform bars
            self.bars = []
            self.bar_layers = []
            num_bars = 5
            bar_width = 3
            bar_spacing = 2
            total_width = num_bars * bar_width + (num_bars - 1) * bar_spacing
            start_x = (frame.size.width - total_width) / 2
            
            for i in range(num_bars):
                bar = Quartz.CALayer.layer()
                bar_x = start_x + i * (bar_width + bar_spacing)
                min_height = 4
                bar.setFrame_(((bar_x, (frame.size.height - min_height) / 2), (bar_width, min_height)))
                bar.setCornerRadius_(bar_width / 2)
                bar.setBackgroundColor_(Cocoa.NSColor.systemRedColor().CGColor())
                self.layer().addSublayer_(bar)
                self.bar_layers.append(bar)
                self.bars.append(min_height)
            
            # Animation offsets for natural movement
            self.phase_offsets = [0, 0.3, 0.6, 0.3, 0]
            self.currentLevel = 0.0
            
        return self
    
    def updateLevel_(self, level):
        """Update waveform bars based on audio level (0.0-1.0)."""
        self.currentLevel = level
        max_height = self.bounds().size.height - 4
        min_height = 4
        
        for i, bar in enumerate(self.bar_layers):
            # Add phase offset for natural wave effect
            offset = self.phase_offsets[i]
            bar_level = min(1.0, level * (1.0 + offset * 0.5))
            
            # Calculate target height
            target_height = min_height + (max_height - min_height) * bar_level
            
            # Animate bar height
            current_frame = bar.frame()
            new_y = (self.bounds().size.height - target_height) / 2
            
            Quartz.CATransaction.begin()
            Quartz.CATransaction.setAnimationDuration_(0.05)
            bar.setFrame_(((current_frame.origin.x, new_y), (current_frame.size.width, target_height)))
            Quartz.CATransaction.commit()


class HUDView(Cocoa.NSView):
    def initWithFrame_(self, frame):
        self = objc.super(HUDView, self).initWithFrame_(frame)
        if self:
            self.setWantsLayer_(True)
            self.layer().setMasksToBounds_(False)  # Allow shadow to spill out
            
            # ===== IMPROVED LAYERED SHADOW =====
            self.layer().setShadowOpacity_(0.4)
            self.layer().setShadowRadius_(12.0)
            self.layer().setShadowOffset_((0, -4))
            self.layer().setShadowColor_(Cocoa.NSColor.blackColor().CGColor())
            
            # ===== MAIN BACKGROUND VIEW =====
            self.effect_view = Cocoa.NSView.alloc().initWithFrame_(self.bounds())
            self.effect_view.setAutoresizingMask_(Cocoa.NSViewWidthSizable | Cocoa.NSViewHeightSizable)
            self.effect_view.setWantsLayer_(True)
            self.effect_view.layer().setCornerRadius_(14.0)
            self.effect_view.layer().setMasksToBounds_(True)
            
            # ===== GRADIENT BACKGROUND LAYER =====
            self.gradient_layer = Quartz.CAGradientLayer.layer()
            self.gradient_layer.setFrame_(((0, 0), (frame.size.width, frame.size.height)))
            self.gradient_layer.setCornerRadius_(14.0)
            
            bottom_color = Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.08, 0.08, 0.10, 0.85)
            top_color = Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.15, 0.15, 0.18, 0.75)
            self.gradient_layer.setColors_([bottom_color.CGColor(), top_color.CGColor()])
            self.gradient_layer.setStartPoint_((0.5, 0.0))
            self.gradient_layer.setEndPoint_((0.5, 1.0))
            self.effect_view.layer().addSublayer_(self.gradient_layer)
            
            # ===== GLASS TOP HIGHLIGHT =====
            self.highlight_layer = Quartz.CALayer.layer()
            highlight_height = 1.5
            self.highlight_layer.setFrame_(((0, frame.size.height - highlight_height), (frame.size.width, highlight_height)))
            highlight_color = Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.15)
            self.highlight_layer.setBackgroundColor_(highlight_color.CGColor())
            self.highlight_layer.setCornerRadius_(14.0)
            self.highlight_layer.setMaskedCorners_(Quartz.kCALayerMinXMaxYCorner | Quartz.kCALayerMaxXMaxYCorner)
            self.effect_view.layer().addSublayer_(self.highlight_layer)
            
            # ===== INNER SHADOW FOR DEPTH =====
            inner_border_color = Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.0, 0.3)
            self.effect_view.layer().setBorderWidth_(0.5)
            self.effect_view.layer().setBorderColor_(inner_border_color.CGColor())
            
            # ===== STATE INDICATOR BORDER (animated) =====
            self.border_layer = Quartz.CALayer.layer()
            self.border_layer.setFrame_(((0, 0), (frame.size.width, frame.size.height)))
            self.border_layer.setCornerRadius_(14.0)
            self.border_layer.setBorderWidth_(2.0)
            self.border_layer.setBorderColor_(Cocoa.NSColor.clearColor().CGColor())
            self.effect_view.layer().addSublayer_(self.border_layer)
            
            self.addSubview_(self.effect_view)
            
            # ===== ICON IMAGE VIEW =====
            icon_size = 18
            icon_y = (frame.size.height - icon_size) / 2.0
            self.icon_view = Cocoa.NSImageView.alloc().initWithFrame_(Cocoa.NSMakeRect(16, icon_y, icon_size, icon_size))
            self.icon_view.setImageScaling_(Cocoa.NSImageScaleProportionallyUpOrDown)
            self.icon_view.setContentTintColor_(Cocoa.NSColor.whiteColor())
            self.icon_view.setWantsLayer_(True)  # Enable layer for spinner animation
            self.effect_view.addSubview_(self.icon_view)
            self.updateIconForState_(AppState.IDLE)
            
            # ===== WAVEFORM VIEW (hidden by default, shown during recording) =====
            waveform_size = 24
            waveform_y = (frame.size.height - waveform_size) / 2.0
            self.waveform_view = WaveformView.alloc().initWithFrame_(Cocoa.NSMakeRect(12, waveform_y, waveform_size, waveform_size))
            self.waveform_view.setHidden_(True)
            self.effect_view.addSubview_(self.waveform_view)
            
            # ===== TEXT LABEL =====
            label_x = 16 + icon_size + 8
            label_width = frame.size.width - label_x - 16
            label_height = 20
            label_y = (frame.size.height - label_height) / 2.0
            self.label = Cocoa.NSTextField.alloc().initWithFrame_(Cocoa.NSMakeRect(label_x, label_y, label_width, label_height))
            self.label.setBezeled_(False)
            self.label.setDrawsBackground_(False)
            self.label.setEditable_(False)
            self.label.setSelectable_(False)
            self.label.setAlignment_(Cocoa.NSTextAlignmentLeft)
            self.label.setFont_(Cocoa.NSFont.systemFontOfSize_weight_(14.0, Cocoa.NSFontWeightSemibold))
            self.label.setTextColor_(Cocoa.NSColor.whiteColor())
            self.label.setStringValue_("Idle")
            
            self.effect_view.addSubview_(self.label)
            
            self.currentState = AppState.IDLE
            self.spinnerAnimation = None
            
        return self

    def updateIconForState_(self, state):
        """Update the SF Symbol icon for the current state."""
        icon_name = STATE_ICONS.get(state, "circle")
        config = Cocoa.NSImageSymbolConfiguration.configurationWithPointSize_weight_scale_(
            16.0, Cocoa.NSFontWeightMedium, Cocoa.NSImageSymbolScaleMedium
        )
        image = Cocoa.NSImage.imageWithSystemSymbolName_accessibilityDescription_(icon_name, None)
        if image:
            image = image.imageWithSymbolConfiguration_(config)
            self.icon_view.setImage_(image)
            
            if state == AppState.RECORDING:
                self.icon_view.setContentTintColor_(Cocoa.NSColor.systemRedColor())
            elif state == AppState.PROCESSING:
                self.icon_view.setContentTintColor_(Cocoa.NSColor.systemBlueColor())
            elif state == AppState.SUCCESS:
                self.icon_view.setContentTintColor_(Cocoa.NSColor.systemGreenColor())
            elif state == AppState.ERROR:
                self.icon_view.setContentTintColor_(Cocoa.NSColor.systemRedColor())
            else:
                self.icon_view.setContentTintColor_(Cocoa.NSColor.whiteColor().colorWithAlphaComponent_(0.7))

    def updateGradientTintForState_(self, state):
        """Update the gradient background with state-specific tint."""
        tint = STATE_TINTS.get(state, STATE_TINTS[AppState.IDLE])
        
        bottom_color = Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(tint[0] * 0.7, tint[1] * 0.7, tint[2] * 0.7, 0.85)
        top_color = Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(tint[0] * 1.3, tint[1] * 1.3, tint[2] * 1.3, 0.75)
        
        Quartz.CATransaction.begin()
        Quartz.CATransaction.setAnimationDuration_(0.3)
        self.gradient_layer.setColors_([bottom_color.CGColor(), top_color.CGColor()])
        Quartz.CATransaction.commit()

    def startSpinner(self):
        """Start pulsing animation for processing state."""
        if self.icon_view.layer():
            layer = self.icon_view.layer()
            
            # Pulsing opacity animation (no anchor point manipulation needed)
            pulse_anim = Cocoa.CABasicAnimation.animationWithKeyPath_("opacity")
            pulse_anim.setFromValue_(1.0)
            pulse_anim.setToValue_(0.4)
            pulse_anim.setDuration_(0.6)
            pulse_anim.setAutoreverses_(True)
            pulse_anim.setRepeatCount_(float("inf"))
            pulse_anim.setTimingFunction_(
                Quartz.CAMediaTimingFunction.functionWithName_(Quartz.kCAMediaTimingFunctionEaseInEaseOut)
            )
            layer.addAnimation_forKey_(pulse_anim, "pulse_processing")

    def stopSpinner(self):
        """Stop the processing animation."""
        if self.icon_view.layer():
            self.icon_view.layer().removeAnimationForKey_("pulse_processing")

    def showWaveform(self):
        """Show waveform and hide icon during recording."""
        self.icon_view.setHidden_(True)
        self.waveform_view.setHidden_(False)

    def hideWaveform(self):
        """Hide waveform and show icon."""
        self.waveform_view.setHidden_(True)
        self.icon_view.setHidden_(False)

    def updateAudioLevel_(self, level):
        """Update waveform with audio level."""
        if not self.waveform_view.isHidden():
            AppHelper.callAfter(self.waveform_view.updateLevel_, level)

    def setStatus_message_(self, state, message):
        self.label.setStringValue_(message)
        self.currentState = state
        self.updateGradientTintForState_(state)
        
        # Handle waveform vs icon visibility
        if state == AppState.RECORDING:
            self.showWaveform()
            self.stopSpinner()
        elif state == AppState.PROCESSING:
            self.hideWaveform()
            self.updateIconForState_(state)
            self.startSpinner()
        else:
            self.hideWaveform()
            self.stopSpinner()
            self.updateIconForState_(state)
        
        # Border animation
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
            self.border_layer.setBorderColor_(color.CGColor())
        elif state == AppState.ERROR:
            color = Cocoa.NSColor.systemRedColor()
            self.stopPulse()
            self.border_layer.setBorderColor_(color.CGColor())
        else:
            self.stopPulse()
            self.border_layer.setBorderColor_(Cocoa.NSColor.clearColor().CGColor())

    def startPulse_(self, ns_color):
        color = ns_color.CGColor()
        self.border_layer.setBorderColor_(color)
        
        anim = Cocoa.CABasicAnimation.animationWithKeyPath_("borderColor")
        anim.setFromValue_(color)
        color_faded = ns_color.colorWithAlphaComponent_(0.3).CGColor()
        anim.setToValue_(color_faded)
        anim.setDuration_(0.8)
        anim.setAutoreverses_(True)
        anim.setRepeatCount_(float("inf"))
        
        self.border_layer.addAnimation_forKey_(anim, "pulse")

    def stopPulse(self):
        self.border_layer.removeAnimationForKey_("pulse")


class HUDController(Cocoa.NSObject):
    def init(self):
        self = objc.super(HUDController, self).init()
        if self:
            # Window dimensions
            self.hudWidth = 200
            self.hudHeight = 48
            rect = Cocoa.NSMakeRect(0, 0, self.hudWidth, self.hudHeight)
            
            style_mask = Cocoa.NSWindowStyleMaskBorderless | Cocoa.NSWindowStyleMaskNonactivatingPanel
            self.window = Cocoa.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                rect, style_mask, Cocoa.NSBackingStoreBuffered, False
            )
            
            self.window.setLevel_(Cocoa.NSScreenSaverWindowLevel)
            self.window.setBackgroundColor_(Cocoa.NSColor.clearColor())
            self.window.setOpaque_(False)
            self.window.setHasShadow_(False)
            self.window.setIgnoresMouseEvents_(True)
            self.window.setFloatingPanel_(True)
            
            # Calculate positions for slide animation
            screen = Cocoa.NSScreen.mainScreen()
            visible_frame = screen.visibleFrame()
            
            self.centerX = visible_frame.origin.x + (visible_frame.size.width - self.hudWidth) / 2
            self.visibleY = visible_frame.origin.y + 100  # Final position
            self.hiddenY = visible_frame.origin.y - self.hudHeight - 20  # Below screen
            
            self.window.setFrameOrigin_((self.centerX, self.hiddenY))
            
            # Set Content View
            self.view = HUDView.alloc().initWithFrame_(rect)
            self.window.setContentView_(self.view)
            
            # Subscribe to state changes
            state_machine.add_observer(self.on_state_change)
            
            # Subscribe to audio level updates
            state_machine.add_audio_level_observer(self.on_audio_level)
            
            # Initially hidden
            self.window.setAlphaValue_(0.0)
            self.window.orderOut_(None)
            self.isVisible = False
            
            # Warmup: briefly show window at 0 alpha to pre-render
            self.performSelector_withObject_afterDelay_(objc.selector(self.warmupHUD, signature=b'v@:'), None, 0.5)
            
        return self

    def warmupHUD(self):
        """Pre-render the HUD window to avoid delay on first display."""
        # Show window invisibly to force rendering
        self.window.setAlphaValue_(0.0)
        self.window.setFrameOrigin_((self.centerX, self.visibleY))
        self.window.orderFront_(None)
        # Hide it again after a brief moment
        self.performSelector_withObject_afterDelay_(objc.selector(self.hideAfterWarmup, signature=b'v@:'), None, 0.1)

    def hideAfterWarmup(self):
        """Hide the HUD after warmup."""
        self.window.orderOut_(None)
        self.window.setFrameOrigin_((self.centerX, self.hiddenY))

    def on_state_change(self, state, data):
        AppHelper.callAfter(self.updateUIForState_data_, state, data)

    def on_audio_level(self, level):
        """Forward audio level to the view."""
        self.view.updateAudioLevel_(level)

    def updateUIForState_data_(self, state, data):
        if state == AppState.IDLE:
            self.slideOut()
        else:
            msg = ""
            if state == AppState.RECORDING:
                msg = "Listening..."
            elif state == AppState.PROCESSING:
                msg = "Processing..."
                if data.get('use_gemini'):
                    msg = "Magic..."
            elif state == AppState.SUCCESS:
                msg = "Copied!"
            elif state == AppState.ERROR:
                msg = data.get('error', "Error!")
            
            self.view.setStatus_message_(state, msg)
            self.slideIn()

    def slideIn(self):
        """Slide up from below screen."""
        if self.isVisible:
            return
        
        self.isVisible = True
        self.window.setFrameOrigin_((self.centerX, self.hiddenY))
        self.window.setAlphaValue_(0.0)
        self.window.orderFront_(None)
        
        # Animate slide up + fade in
        Cocoa.NSAnimationContext.beginGrouping()
        Cocoa.NSAnimationContext.currentContext().setDuration_(0.3)
        Cocoa.NSAnimationContext.currentContext().setTimingFunction_(
            Quartz.CAMediaTimingFunction.functionWithName_(Quartz.kCAMediaTimingFunctionEaseOut)
        )
        self.window.animator().setFrame_display_(
            Cocoa.NSMakeRect(self.centerX, self.visibleY, self.hudWidth, self.hudHeight),
            True
        )
        self.window.animator().setAlphaValue_(1.0)
        Cocoa.NSAnimationContext.endGrouping()

    def slideOut(self):
        """Slide down and fade out."""
        if not self.isVisible:
            return
        
        self.isVisible = False
        
        # Animate slide down + fade out
        Cocoa.NSAnimationContext.beginGrouping()
        Cocoa.NSAnimationContext.currentContext().setDuration_(0.25)
        Cocoa.NSAnimationContext.currentContext().setTimingFunction_(
            Quartz.CAMediaTimingFunction.functionWithName_(Quartz.kCAMediaTimingFunctionEaseIn)
        )
        self.window.animator().setFrame_display_(
            Cocoa.NSMakeRect(self.centerX, self.hiddenY, self.hudWidth, self.hudHeight),
            True
        )
        self.window.animator().setAlphaValue_(0.0)
        Cocoa.NSAnimationContext.endGrouping()
