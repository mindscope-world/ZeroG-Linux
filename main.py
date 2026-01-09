import sys
import os
from PyQt6.QtWidgets import QApplication
from zerog.gui.hud import LinuxHUD
from zerog.core.state import state_machine

def main():
    # 1. Initialize the Qt Application
    # This must happen before any GUI elements are created
    app = QApplication(sys.argv)
    app.setApplicationName("ZeroG")

    # 2. Setup the GUI
    # We create the window instance and show it immediately
    hud = LinuxHUD()
    hud.show()

    # 3. Print status for the user in the terminal
    print("🛰️ ZeroG is in orbit.")
    print("Click 'Start Recording' in the GUI to begin.")

    # 4. Start the Event Loop
    # This keeps the app running until you close the window.
    # Without this line, the window would flash for a millisecond and disappear.
    sys.exit(app.exec())

if __name__ == "__main__":
    main()