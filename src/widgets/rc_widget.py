"""
RC Input Widget - Displays RC channel values.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer


class RCChannelBar(QWidget):
    """Vertical progress bar for a single RC channel."""
    
    def __init__(self, channel_num, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        
        # Value label at top
        self.value_label = QLabel("1500")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("color: #aaa; font-size: 10px; font-weight: bold;")
        layout.addWidget(self.value_label)
        
        # Progress bar
        self.bar = QProgressBar()
        self.bar.setOrientation(Qt.Vertical)
        self.bar.setRange(1000, 2000)
        self.bar.setValue(1500)
        self.bar.setTextVisible(False)
        self.bar.setStyleSheet("""
            QProgressBar {
                background-color: #2b2b40;
                border: 1px solid #3d3d5c;
                border-radius: 4px;
                width: 24px;  /* Wider bars */
            }
            QProgressBar::chunk {
                background-color: #6c63ff;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.bar, 1)  # Expand vertically
        
        # Channel label at bottom
        self.label = QLabel(f"CH{channel_num}")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        layout.addWidget(self.label)
        
    def set_value(self, value):
        self.bar.setValue(value)
        self.value_label.setText(str(value))


class RCWidget(QWidget):
    """Widget displaying 8 RC channels."""
    
    def __init__(self, message_broker, parent=None):
        super().__init__(parent)
        self.message_broker = message_broker
        self.channels = []
        self._setup_ui()
        
        # Buffer for latest RC values
        self._latest_values = [1500] * 8
        self._pending_update = False
        
        # Optimize: 10Hz update rate
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100) # 10Hz
        
        self._subscribe_to_messages()
        
    def _setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Title
        header = QLabel("RC INPUTS")
        header.setStyleSheet("font-size: 11px; font-weight: bold; color: #666; letter-spacing: 1px;")
        main_layout.addWidget(header)
        
        # Container for bars
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #1e1e2f;
                border-radius: 8px;
            }
        """)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(8)
        
        # Create 8 channel bars
        for i in range(1, 9):
            bar = RCChannelBar(i)
            self.channels.append(bar)
            container_layout.addWidget(bar)
            
        main_layout.addWidget(container, 1)
        
    def _subscribe_to_messages(self):
        self.message_broker.subscribe('RC_CHANNELS', self._on_rc_channels)
        
    def _on_rc_channels(self, msg):
        """Handle RC_CHANNELS message."""
        # Just update buffer, logic in timer
        self._latest_values = [
            msg.chan1_raw, msg.chan2_raw, msg.chan3_raw, msg.chan4_raw,
            msg.chan5_raw, msg.chan6_raw, msg.chan7_raw, msg.chan8_raw
        ]
        self._pending_update = True
    
    def _update_display(self):
        """Timer callback to update UI."""
        if not self._pending_update or not self.isVisible():
            return
            
        for i, val in enumerate(self._latest_values):
            if i < len(self.channels):
                # Clamp value
                val = max(1000, min(2000, val))
                self.channels[i].set_value(val)
        
        self._pending_update = False
