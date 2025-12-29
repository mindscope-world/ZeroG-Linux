import Cocoa
import objc
from macdictate.core.recorder import AudioRecorder
from macdictate.core.input import KeyMonitor
from macdictate.gui.menu import StatusMenuController
from macdictate.gui.hud import HUDController

class MacDictateApp(Cocoa.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        # Initialize Core Logic
        self.recorder = AudioRecorder()
        self.key_monitor = KeyMonitor()
        self.key_monitor.start()
        
        # Initialize UI
        self.menu_controller = StatusMenuController.alloc().init()
        self.hud_controller = HUDController.alloc().init()
        
        print("MacDictate Started (Native Mode)")

def run():
    app = Cocoa.NSApplication.sharedApplication()
    delegate = MacDictateApp.alloc().init()
    app.setDelegate_(delegate)
    app.run()
