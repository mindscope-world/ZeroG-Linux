# main.py
import sys
from PyQt6.QtWidgets import QApplication
from zerog.gui.hud import LinuxHUD
from zerog.core.input import KeyMonitor

def main():
    # Create the application instance first
    app = QApplication(sys.argv)
    
    # STEP 1: Create and Show the window immediately
    hud = LinuxHUD() 
    hud.show() 
    
    # STEP 2: Start the keyboard listener ONLY after the window is up
    monitor = KeyMonitor()
    monitor.start()
    
    print("🛰️ ZeroG is in orbit. Control Panel should be visible.")
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()