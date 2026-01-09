import sys
import threading
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSlot
from pynput import keyboard

class ZeroGMini(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZeroG Mini-Controller")
        self.setFixedSize(300, 150)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint) # Keep it visible

        # UI Elements
        self.label = QLabel("Status: Idle", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button = QPushButton("🔴 Start Recording", self)
        self.button.setMinimumHeight(60)
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Thread-safe state tracking
        self.is_recording = False

    def update_status(self, text, color):
        self.label.setText(f"Status: {text}")
        self.button.setText("⏹️ Stop" if "Recording" in text else "🔴 Start Recording")
        self.button.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold;")

def start_keyboard_listener(window_ref):
    """Runs in a separate thread so it doesn't block the GUI"""
    def on_press(key):
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl:
            window_ref.update_status("Recording...", "#ff4444")
            
    def on_release(key):
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl:
            window_ref.update_status("Processing...", "#4444ff")
            # Logic to return to idle after a delay
            threading.Timer(2.0, lambda: window_ref.update_status("Idle", "none")).start()

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. Launch GUI
    win = ZeroGMini()
    win.show()
    
    # 2. Launch Keyboard Monitor in Background Thread
    monitor_thread = threading.Thread(target=start_keyboard_listener, args=(win,), daemon=True)
    monitor_thread.start()
    
    print("🚀 Mini-App is running. GUI should be visible now!")
    sys.exit(app.exec())