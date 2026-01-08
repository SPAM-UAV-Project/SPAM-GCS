"""
Settings Page - Sensor calibration controls.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGridLayout
)
from PyQt5.QtCore import Qt


class SettingsPage(QWidget):
    """Settings page with sensor calibration controls."""
    
    def __init__(self, message_broker, mavlink_manager, parent=None):
        super().__init__(parent)
        self.message_broker = message_broker
        self.mavlink_manager = mavlink_manager
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Calibration section
        calib_title = QLabel("Sensor Calibration")
        calib_title.setObjectName("sectionTitle")
        layout.addWidget(calib_title)
        
        # Calibration cards
        calib_layout = QHBoxLayout()
        calib_layout.setSpacing(16)
        
        calibrations = [
            ("Accelerometer", "Hold vehicle in each of 6 orientations:\nLevel → Nose Down → Nose Up →\nLeft Side → Right Side → Upside Down"),
            ("Gyroscope", "Keep vehicle completely\nstationary during calibration."),
            ("Magnetometer", "Rotate vehicle through all\norientations until complete."),
        ]
        
        self.calib_status_labels = {}
        self.calib_buttons = {}
        
        for name, instructions in calibrations:
            card = QFrame()
            card.setObjectName("statusCard")
            card_layout = QVBoxLayout(card)
            
            card_title = QLabel(name)
            card_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #a0a0ff;")
            card_layout.addWidget(card_title)
            
            instr_label = QLabel(instructions)
            instr_label.setStyleSheet("color: #888; font-size: 11px;")
            instr_label.setWordWrap(True)
            card_layout.addWidget(instr_label)
            
            card_layout.addStretch()
            
            status_label = QLabel("Status: Idle")
            status_label.setStyleSheet("color: #666;")
            self.calib_status_labels[name.lower()] = status_label
            card_layout.addWidget(status_label)
            
            start_btn = QPushButton("Start Calibration")
            start_btn.setEnabled(False)  # Disabled until connected
            self.calib_buttons[name.lower()] = start_btn
            card_layout.addWidget(start_btn)
            
            calib_layout.addWidget(card)
        
        layout.addLayout(calib_layout)
        layout.addStretch()
    
    def set_connected(self, connected: bool):
        """Enable/disable calibration buttons based on connection status."""
        for btn in self.calib_buttons.values():
            btn.setEnabled(connected)
