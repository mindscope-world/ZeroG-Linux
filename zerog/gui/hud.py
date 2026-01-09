import sys
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSlot
from zerog.core.state import state_machine, AppState
from PyQt6.QtCore import QTimer

class LinuxHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZeroG Control")
        self.setFixedSize(300, 150)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        # UI Elements
        self.status_label = QLabel("STATUS: IDLE", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.action_button = QPushButton("🔴 Start Recording", self)
        self.action_button.setMinimumHeight(60)
        
        # Connect the click event to our logic
        self.action_button.clicked.connect(self.handle_button_click)
        
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.action_button)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # Watch for state changes (e.g., if the key actually DOES work later)
        state_machine.add_observer(self.on_state_changed)
        self.show()

    @pyqtSlot()
    def handle_button_click(self):
        """Toggle recording state based on current state"""
        current = state_machine.current_state
        
        if current == AppState.IDLE:
            # Start the recording
            state_machine.set_state(AppState.RECORDING)
        elif current == AppState.RECORDING:
            # Stop recording and start processing audio
            state_machine.set_state(AppState.PROCESSING)

    # Inside the LinuxHUD class:
    def on_state_changed(self, state, data=None):
        self.status_label.setText(f"STATUS: {state.name}")
        
        if state == AppState.PROCESSING:
            self.action_button.setText("⏳ Processing...")
            self.action_button.setEnabled(False)
            # Safety: Reset if stuck for 30 seconds
            QTimer.singleShot(30000, self.reset_if_stuck)
            
        elif state == AppState.IDLE:
            self.action_button.setText("🔴 Start Recording")
            self.action_button.setEnabled(True)
            self.action_button.setStyleSheet("")
    
    def reset_if_stuck(self):
        if state_machine.current_state == AppState.PROCESSING:
            self.status_label.setText("STATUS: ERROR/TIMEOUT")
            self.action_button.setEnabled(True)
            self.action_button.setText("🔄 Try Again")
