import Cocoa
import objc
import Quartz
import WebKit
import logging
from PyObjCTools import AppHelper
from zerog.core.state import state_machine, AppState

logger = logging.getLogger(__name__)

HTML_CONTENT = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        @keyframes spin-slow { to { transform: rotate(360deg); } }
        @keyframes spin-fast { to { transform: rotate(360deg); } }
        @keyframes pulse-slow { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
            20%, 40%, 60%, 80% { transform: translateX(2px); }
        }
        .orbit-ring { animation: spin-slow 3s linear infinite; }
        .processing-ring { animation: spin-fast 1s linear infinite; }
        .shake-anim { animation: shake 0.4s cubic-bezier(.36,.07,.19,.97) both; }
        #recorder-interface { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        /* Void Black Background */
        body { background: transparent !important; margin: 0; padding: 0; overflow: hidden; display: flex; align-items: center; justify-content: center; height: 100vh; width: 100vw; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
    </style>
</head>
<body class="font-mono">
    <!-- Main Container: Void Black Background, Vacuum Grey Border -->
    <div id="recorder-interface" class="w-[210px] h-[48px] bg-[#0b0b0b] rounded-full flex items-center px-2 relative border border-[#333333] select-none overflow-hidden transition-all duration-75">
    </div>

    <script>
        const container = document.getElementById('recorder-interface');
        let currentState = 'recording';
        const states = {
            recording: {
                shadow: 'shadow-none', 
                border: 'border-[#333333]',
                html: `
                    <!-- Warning Yellow Glow -->
                    <div id="glow-ring" class="absolute inset-0 rounded-full transition-all duration-75 ease-out opacity-0 pointer-events-none" style="z-index: -1; box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);"></div>
                    
                    <div class="w-10 h-10 rounded-full relative flex items-center justify-center flex-shrink-0 z-10">
                        <div class="absolute inset-0 rounded-full border border-[#FFD700]/30"></div>
                        <div class="absolute inset-0 rounded-full border-t-2 border-r-2 border-transparent border-t-[#FFD700] border-r-[#FFD700] orbit-ring"></div>
                        <svg class="w-4 h-4 text-[#FFD700]" fill="currentColor" viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
                    </div>
                    <div class="flex flex-col items-start justify-center leading-none ml-2 z-10">
                        <span class="text-[9px] text-[#EDEDED] opacity-60 font-bold uppercase tracking-wider mb-0.5">ZeroG Link</span>
                        <span id="label-text" class="text-xs font-bold text-[#FFD700] tracking-widest uppercase">TRANSMITTING...</span>
                    </div>
                `
            },
            processing: {
                shadow: 'shadow-[0_0_25px_rgba(255,215,0,0.3)]',
                border: 'border-[#FFD700]/30',
                html: `
                    <div class="w-10 h-10 rounded-full relative flex items-center justify-center flex-shrink-0">
                         <div class="absolute inset-0 rounded-full border border-[#FFD700]/20"></div>
                         <div class="absolute inset-0 rounded-full border-2 border-transparent border-l-[#FFD700] border-r-[#EDEDED] processing-ring"></div>
                         <svg class="w-4 h-4 text-[#EDEDED]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                             <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z" />
                         </svg>
                    </div>
                    <div class="flex flex-col items-start justify-center leading-none ml-2">
                        <span class="text-[9px] text-[#EDEDED] opacity-60 font-bold uppercase tracking-wider mb-0.5">PROCESSING</span>
                        <span id="label-text" class="text-xs font-bold text-[#EDEDED] animate-pulse uppercase tracking-widest">CALCULATING...</span>
                    </div>
                `
            },
            success: {
                shadow: 'shadow-[0_0_20px_rgba(16,185,129,0.4)]',
                border: 'border-emerald-500/30',
                html: `
                    <div class="w-10 h-10 rounded-full relative flex items-center justify-center bg-emerald-500/10 flex-shrink-0">
                         <div class="absolute inset-0 rounded-full border border-emerald-500/50 scale-100 animate-[ping_1s_cubic-bezier(0,0,0.2,1)_1]"></div>
                         <svg class="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                             <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                         </svg>
                    </div>
                    <div class="flex flex-col items-start justify-center leading-none ml-2">
                        <span id="label-text" class="text-xs font-bold text-emerald-400 uppercase tracking-widest">ESTABLISHED</span>
                    </div>
                `
            },
            error: {
                shadow: 'shadow-[0_0_20px_rgba(244,63,94,0.4)]',
                border: 'border-rose-500/30',
                html: `
                    <div class="w-10 h-10 rounded-full relative flex items-center justify-center bg-rose-500/10 flex-shrink-0">
                         <svg class="w-5 h-5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                             <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                         </svg>
                    </div>
                    <div class="flex flex-col items-start justify-center leading-none ml-2">
                        <span class="text-[9px] text-rose-400/70 font-bold uppercase tracking-wider mb-0.5">TURBULENCE</span>
                        <span id="label-text" class="text-xs font-bold text-rose-200 uppercase tracking-widest">ABORTED</span>
                    </div>
                `
            }
        };

        window.setState = function(stateName, message) {
            const config = states[stateName];
            if (!config) return;
            
            currentState = stateName;
            container.className = `w-[210px] h-[48px] bg-[#0b0b0b] rounded-full flex items-center px-2 relative transition-all duration-75 select-none overflow-visible ${config.shadow} ${config.border}`;
            
            if (stateName === 'error') {
                container.classList.add('shake-anim');
                setTimeout(() => container.classList.remove('shake-anim'), 400);
            }

            container.innerHTML = config.html;
            if (message) {
                const label = document.getElementById('label-text');
                if (label) label.innerText = message;
            }
        };

        let lastIntensity = 0;
        window.applyShadow = function(intensity) {
            if (currentState !== 'recording') return;
            
            const glow = document.getElementById('glow-ring');
            if (!glow) return;

            const isAttack = intensity > lastIntensity;
            const duration = isAttack ? '120ms' : '600ms'; 
            
            glow.style.transition = `all ${duration} ease-out`;

            const BASE_SIZE = 0;
            const MAX_EXTRA = 60;
            const size = BASE_SIZE + (intensity * MAX_EXTRA);
            const opacity = 0.3 + (intensity * 0.7); 
            
            // Gold glow rgba(255, 215, 0, ...)
            glow.style.boxShadow = `0 0 ${20 + size}px ${5 + (size/2)}px rgba(255, 215, 0, ${opacity})`;
            glow.style.opacity = opacity;
            
            lastIntensity = intensity;
        };

        console.log("JS Ready");
        window.setState('recording', 'Ready');
    </script>
</body>
</html>
"""

class HUDView(WebKit.WKWebView):
    def initWithFrame_(self, frame):
        config = WebKit.WKWebViewConfiguration.alloc().init()
        
        self = objc.super(HUDView, self).initWithFrame_configuration_(frame, config)
        if self:
            self.setWantsLayer_(True)
            # Make webview transparent
            self.setValue_forKey_(False, "drawsBackground")
            if hasattr(self, 'setUnderPageBackgroundColor_'):
                self.setUnderPageBackgroundColor_(Cocoa.NSColor.clearColor())
            
            # Set navigation delegate for intercepting URL schemes
            self.setNavigationDelegate_(self)
            
            # Load content
            self.loadHTMLString_baseURL_(HTML_CONTENT, None)
            logger.info("HUDView initialized and HTML loaded.")
            
        return self

    def acceptsFirstMouse_(self, event):
        return True

    def webView_decidePolicyForNavigationAction_decisionHandler_(self, webView, navigationAction, decisionHandler):
        """Intercept app:// custom schemes."""
        url = navigationAction.request().URL().absoluteString()
        if url.startswith("app://stopRecording"):
            logger.info("HUD: Stop button clicked.")
            app_delegate = Cocoa.NSApp.delegate()
            if app_delegate and hasattr(app_delegate, 'recorder'):
                app_delegate.recorder.stop_recording()
            
            # Cancel navigation
            decisionHandler(WebKit.WKNavigationActionPolicyCancel)
            return

        # Allow other navigation (should be none for this app)
        decisionHandler(WebKit.WKNavigationActionPolicyAllow)

    def evaluate_js(self, script):
        """Helper to run JS in the webview on the main thread."""
        def _completion_handler(result, error):
            if error:
                logger.error(f"JS Error: {error}")
        
        def _run():
            self.evaluateJavaScript_completionHandler_(script, _completion_handler)
        AppHelper.callAfter(_run)

    def setStatus_message_(self, state, message):
        """Map AppState to JS state."""
        js_state = "recording"
        if state == AppState.RECORDING:
            js_state = "recording"
        elif state == AppState.PROCESSING:
            js_state = "processing"
        elif state == AppState.SUCCESS:
            js_state = "success"
        elif state == AppState.ERROR:
            js_state = "error"
        else:
            js_state = "recording"
            
        safe_msg = message.replace("'", "\\'")
        logger.debug(f"HUD: Calling setState('{js_state}', '{safe_msg}')")
        self.evaluate_js(f"window.setState('{js_state}', '{safe_msg}')")

    def updateAudioLevel_(self, level):
        """Forward audio level to JS bridge."""
        # Log RAW level to verify input
        # logger.debug(f"HUD RAW Level: {level}") 
        
        # Boost level for better visibility and clamp to 1.0
        display_level = min(1.0, level * 5.0)
        
        if display_level > 0.0:
            # logger.debug(f"HUD Audio Level: {level:.3f} -> {display_level:.3f}")
            pass
        self.evaluate_js(f"window.applyShadow({display_level:.2f})")


class HUDController(Cocoa.NSObject):
    def init(self):
        self = objc.super(HUDController, self).init()
        if self:
            # Window dimensions
            self.hudWidth = 525 # Increased +50% to 525 (was 350)
            self.hudHeight = 300 # Increased +50% to 300 (was 200)
            
            rect = Cocoa.NSMakeRect(0, 0, self.hudWidth, self.hudHeight)
            
            style_mask = Cocoa.NSWindowStyleMaskBorderless | Cocoa.NSWindowStyleMaskNonactivatingPanel
            self.window = Cocoa.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                rect, style_mask, Cocoa.NSBackingStoreBuffered, False
            )
            
            # Use a very high level to ensure visibility
            self.window.setLevel_(Cocoa.NSScreenSaverWindowLevel + 1)
            self.window.setBackgroundColor_(Cocoa.NSColor.clearColor())
            self.window.setOpaque_(False)
            self.window.setHasShadow_(False)
            # Enable mouse events only when visible (set to True initially for click-through)
            self.window.setIgnoresMouseEvents_(True) 
            self.window.setFloatingPanel_(True)
            self.window.setHidesOnDeactivate_(False)
            self.window.setCanHide_(False)
            self.window.setCollectionBehavior_(
                Cocoa.NSWindowCollectionBehaviorCanJoinAllSpaces | 
                Cocoa.NSWindowCollectionBehaviorStationary |
                Cocoa.NSWindowCollectionBehaviorIgnoresCycle
            )
            
            # Calculate positions
            screen = Cocoa.NSScreen.mainScreen()
            visible_frame = screen.visibleFrame()
            
            self.centerX = visible_frame.origin.x + (visible_frame.size.width - self.hudWidth) / 2
            self.visibleY = visible_frame.origin.y + 120
            self.hiddenY = visible_frame.origin.y - self.hudHeight - 50
            
            self.window.setFrameOrigin_((self.centerX, self.hiddenY))
            
            # Use current content view bounds
            self.view = HUDView.alloc().initWithFrame_(self.window.contentView().bounds())
            self.window.setContentView_(self.view)
            
            # Subscribe to events
            state_machine.add_observer(self.on_state_change)
            state_machine.add_audio_level_observer(self.on_audio_level)
            
            self.window.setAlphaValue_(0.0)
            self.window.orderOut_(None)
            self.isVisible = False
            
            logger.info("HUDController initialized.")
            
        return self

    def update_position(self):
        """Update HUD position based on current mouse location."""
        # Find screen with mouse
        mouse_loc = Cocoa.NSEvent.mouseLocation()
        target_screen = None
        
        for screen in Cocoa.NSScreen.screens():
            if Cocoa.NSPointInRect(mouse_loc, screen.frame()):
                target_screen = screen
                break
        
        # Fallback to main screen if mouse is off-screen (shouldn't happen often)
        if not target_screen:
            target_screen = Cocoa.NSScreen.mainScreen()
            
        visible_frame = target_screen.visibleFrame()
        
        # Recalculate positions relative to target screen
        self.centerX = visible_frame.origin.x + (visible_frame.size.width - self.hudWidth) / 2
        self.visibleY = visible_frame.origin.y + 120
        self.hiddenY = visible_frame.origin.y - self.hudHeight - 50
        
        logger.debug(f"HUD Position Updated: Screen={target_screen.localizedName()}, CenterX={self.centerX}, VisibleY={self.visibleY}")

    def on_state_change(self, state, data):
        AppHelper.callAfter(self.updateUIForState_data_, state, data)

    def on_audio_level(self, level):
        # Dispatch to main thread immediately
        # if level > 0.01: logger.debug("HUDController.on_audio_level called")
        AppHelper.callAfter(self.view.updateAudioLevel_, level)

    def updateUIForState_data_(self, state, data):
        logger.debug(f"HUD: on_state_change({state})")
        if state == AppState.IDLE:
            self.slideOut()
        else:
            msg = "Listening..."
            if state == AppState.RECORDING:
                msg = "Listening..."
            elif state == AppState.PROCESSING:
                msg = "Magic..." if data.get('use_gemini') else "Processing..."
            elif state == AppState.SUCCESS:
                msg = "Copied!"
            elif state == AppState.ERROR:
                msg = data.get('error', "Error!")
            
            self.view.setStatus_message_(state, msg)
            self.slideIn()

    def slideIn(self):
        # Cancel any pending hide requests
        Cocoa.NSObject.cancelPreviousPerformRequestsWithTarget_selector_object_(
            self, objc.selector(self.window.orderOut_, signature=b'v@:@'), None
        )
        
        if self.isVisible: 
            self.window.orderFrontRegardless()
            return

        # Update position based on current mouse screen
        self.update_position()

        self.isVisible = True
        logger.info(f"HUD sliding in to ({self.centerX}, {self.visibleY})...")
        
        # ENABLE mouse events for interaction
        # self.window.setIgnoresMouseEvents_(False)
        
        # Start slightly below target for a subtle slide up
        start_y = self.visibleY - 20
        self.window.setFrameOrigin_((self.centerX, start_y))
        self.window.setAlphaValue_(0.0)
        self.window.orderFrontRegardless()
        
        Cocoa.NSAnimationContext.beginGrouping()
        Cocoa.NSAnimationContext.currentContext().setDuration_(0.3)
        Cocoa.NSAnimationContext.currentContext().setTimingFunction_(
            Quartz.CAMediaTimingFunction.functionWithName_(Quartz.kCAMediaTimingFunctionEaseOut)
        )
        self.window.animator().setFrameOrigin_((self.centerX, self.visibleY))
        self.window.animator().setAlphaValue_(1.0)
        Cocoa.NSAnimationContext.endGrouping()

    def slideOut(self):
        if not self.isVisible: return
        self.isVisible = False
        logger.info("HUD sliding out...")
        
        # DISABLE mouse events (allow click-through) immediately
        self.window.setIgnoresMouseEvents_(True)
        
        Cocoa.NSAnimationContext.beginGrouping()
        Cocoa.NSAnimationContext.currentContext().setDuration_(0.25)
        Cocoa.NSAnimationContext.currentContext().setTimingFunction_(
            Quartz.CAMediaTimingFunction.functionWithName_(Quartz.kCAMediaTimingFunctionEaseIn)
        )
        self.window.animator().setFrameOrigin_((self.centerX, self.hiddenY))
        self.window.animator().setAlphaValue_(0.0)
        Cocoa.NSAnimationContext.endGrouping()
        
        # Order out after animation
        self.performSelector_withObject_afterDelay_(objc.selector(self.window.orderOut_, signature=b'v@:@'), None, 0.25)
