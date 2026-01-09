import sys
import os
# Force unbuffered logs so you can finally see them in the terminal
os.environ["PYTHONUNBUFFERED"] = "1"

from PyQt6.QtWidgets import QApplication
from zerog.gui.hud import LinuxHUD
from zerog.core.recorder import AudioRecorder

def main():
    print("🛰️  ZeroG is initializing...")
    app = QApplication(sys.argv)
    
    # Initialize the recorder FIRST
    # This matches your debug_model.py success
    recorder = AudioRecorder() 
    
    # Initialize the HUD
    hud = LinuxHUD()
    hud.show()
    
    print("🚀 ZeroG is in orbit. Ready for input.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()