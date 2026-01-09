import sys
from PyQt6.QtWidgets import QApplication
from zerog.core.recorder import AudioRecorder
from zerog.core.input import KeyMonitor
from zerog.core.menu import StatusMenuController
from zerog.core.hud import HUDController

def run():
    # Initialize the Qt Application Loop
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Initialize Core (Non-UI)
    recorder = AudioRecorder()
    key_monitor = KeyMonitor()
    key_monitor.start()
    
    # Initialize UI (PyQt6 versions)
    menu_controller = StatusMenuController(app)
    hud_controller = HUDController()
    
    print("ZeroG Started (Linux Mode)")
    
    # Start the event loop
    sys.exit(app.exec())