import Cocoa
import objc
from PyObjCTools import AppHelper
from macdictate.core.state import state_machine, AppState

class StatusMenuController(Cocoa.NSObject):
    def init(self):
        self = objc.super(StatusMenuController, self).init()
        if self:
            self.status_item = Cocoa.NSStatusBar.systemStatusBar().statusItemWithLength_(Cocoa.NSVariableStatusItemLength)
            
            # Build Menu
            self.menu = Cocoa.NSMenu.alloc().init()
            
            self.quit_item = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Quit MacDictate", "terminate:", "q"
            )
            self.menu.addItem_(self.quit_item)
            
            self.status_item.setMenu_(self.menu)
            self.update_icon(AppState.IDLE)
            
            # Subscribe to State Changes
            state_machine.add_observer(self.on_state_change)
        return self

    def on_state_change(self, state, data):
        # UI updates must happen on Main Thread
        AppHelper.callAfter(self.update_icon, state)

    def update_icon(self, state):
        button = self.status_item.button()
        if not button: return
        
        symbol_name = "mic"
        color = Cocoa.NSColor.labelColor()
        
        if state == AppState.IDLE:
            symbol_name = "mic"
        elif state == AppState.RECORDING:
            symbol_name = "mic.fill"
            color = Cocoa.NSColor.systemRedColor()
        elif state == AppState.PROCESSING:
            symbol_name = "waveform.circle" # or ellipsis.bubble
        elif state == AppState.SUCCESS:
            symbol_name = "checkmark.circle"
            color = Cocoa.NSColor.systemGreenColor()
        elif state == AppState.ERROR:
            symbol_name = "exclamationmark.triangle"
            color = Cocoa.NSColor.systemYellowColor()

        image = Cocoa.NSImage.imageWithSystemSymbolName_accessibilityDescription_(symbol_name, "MacDictate Status")
        if image:
            image.setTemplate_(True) # Helps with dark/light mode
            
            # For coloring (Red/Green), we might need a distinct configuration or creating a tinted image.
            # setTemplate(True) makes it adapt to system text color. 
            # If we really want Red, we need setTemplate(False) and tint it.
            # For simplicity in V1, let's stick to standard behavior or simple image assignment.
            # If color != labelColor, we can try to tint.
            
            if color != Cocoa.NSColor.labelColor():
                # Simple tinting approach for SF Symbols is Tricky in PyObjC without more logic.
                # We'll use setTemplate(False) if we want specific color, but image must contain color?
                # SF Symbols are usually monochrome unless multi-color.
                # Let's keep it simple: just the icon change is enough for now.
                pass

        button.setImage_(image)
