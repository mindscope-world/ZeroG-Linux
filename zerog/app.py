import Cocoa
import objc
from zerog.core.recorder import AudioRecorder
from zerog.core.input import KeyMonitor
from zerog.gui.menu import StatusMenuController
from zerog.gui.hud import HUDController

class ZeroGApp(Cocoa.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        # Initialize Core Logic
        self.recorder = AudioRecorder()
        self.key_monitor = KeyMonitor()
        self.key_monitor.start()
        
        # Initialize UI
        self.menu_controller = StatusMenuController.alloc().init()
        self.hud_controller = HUDController.alloc().init()
        
        print("ZeroG Started (Native Mode)")

def run():
    app = Cocoa.NSApplication.sharedApplication()
    delegate = ZeroGApp.alloc().init()
    app.setDelegate_(delegate)
    app.run()
