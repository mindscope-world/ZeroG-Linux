import sys
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSlot
from zerog.core.state import state_machine, AppState

class LinuxHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZeroG Control")
        self.setFixedSize(300, 150)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        # UI Elements
        self.status_label = QLabel("STATUS: IDLE", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: white;")
        
        self.action_button = QPushButton("🔴 Start Recording", self)
        self.action_button.setMinimumHeight(60)
        
        # Connect click event
        self.action_button.clicked.connect(self.handle_button_click)
        
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.action_button)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # Subscribe to state changes
        state_machine.add_observer(self.on_state_changed)
        self.show()

    @pyqtSlot()
    def handle_button_click(self):
        """Toggle between states based on current app state"""
        current = state_machine.current_state
        if current == AppState.IDLE or current == AppState.SUCCESS or current == AppState.ERROR:
            state_machine.set_state(AppState.RECORDING)
        elif current == AppState.RECORDING:
            state_machine.set_state(AppState.PROCESSING)

    def on_state_changed(self, state, data=None):
        """Updates the button text and color based on the state"""
        self.status_label.setText(f"STATUS: {state.name}")
        
        if state == AppState.RECORDING:
            # Change to Stop when recording
            self.action_button.setText("⏹️ Stop Recording")
            self.action_button.setStyleSheet("background-color: #ff4c4c; color: white; font-weight: bold;")
        
        elif state == AppState.PROCESSING:
            self.action_button.setText("⏳ Processing...")
            self.action_button.setEnabled(False)
            self.action_button.setStyleSheet("background-color: #555555; color: #aaaaaa;")
            
        elif state == AppState.SUCCESS:
            self.action_button.setText("✅ Success!")
            self.action_button.setEnabled(False)
            self.action_button.setStyleSheet("background-color: #2e7d32; color: white;")
            
        elif state == AppState.IDLE:
            self.action_button.setText("🔴 Start Recording")
            self.action_button.setEnabled(True)
            self.action_button.setStyleSheet("")