"""
RC Input Widget - Compact display of RC channel values.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
)
from PyQt5.QtCore import Qt


class RCWidget(QWidget):
    """
    Compact RC channel display with vertical progress bars.
    Shows channels 1-8 with values 1000-2000.
    """
    
    RC_MIN = 1000
    RC_MAX = 2000
    RC_MID = 1500
    
    def __init__(self, message_broker, parent=None):
        super().__init__(parent)
        self.message_broker = message_broker
        self.channel_bars = []
        self.channel_labels = []
        
        self._setup_ui()
        self._subscribe_to_messages()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Title
        title = QLabel("RC")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 11px; color: #a0a0ff;")
        layout.addWidget(title)
        
        # Channel displays
        for i in range(1, 9):
            ch_layout = QHBoxLayout()
            ch_layout.setSpacing(4)
            
            # Channel number
            ch_label = QLabel(f"{i}")
            ch_label.setFixedWidth(12)
            ch_label.setAlignment(Qt.AlignCenter)
            ch_label.setStyleSheet("color: #888; font-size: 10px;")
            ch_layout.addWidget(ch_label)
            
            # Progress bar
            bar = QProgressBar()
            bar.setMinimum(self.RC_MIN)
            bar.setMaximum(self.RC_MAX)
            bar.setValue(self.RC_MID)
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            bar.setStyleSheet("""
                QProgressBar {
                    background-color: #1a1a2e;
                    border: 1px solid #3a3a5c;
                    border-radius: 2px;
                }
                QProgressBar::chunk {
                    background-color: #6c63ff;
                    border-radius: 1px;
                }
            """)
            ch_layout.addWidget(bar)
            
            # Value label
            val_label = QLabel("1500")
            val_label.setFixedWidth(32)
            val_label.setAlignment(Qt.AlignRight)
            val_label.setStyleSheet(
                "color: #888; font-size: 9px; font-family: 'Consolas', monospace;"
            )
            ch_layout.addWidget(val_label)
            
            self.channel_bars.append(bar)
            self.channel_labels.append(val_label)
            
            layout.addLayout(ch_layout)
        
        layout.addStretch()
    
    def _subscribe_to_messages(self):
        """Subscribe to RC channel messages."""
        self.message_broker.subscribe('RC_CHANNELS', self._on_rc_channels)
        self.message_broker.subscribe('RC_CHANNELS_RAW', self._on_rc_channels_raw)
    
    def _on_rc_channels(self, msg):
        """Handle RC_CHANNELS message."""
        channels = [
            msg.chan1_raw, msg.chan2_raw, msg.chan3_raw, msg.chan4_raw,
            msg.chan5_raw, msg.chan6_raw, msg.chan7_raw, msg.chan8_raw
        ]
        self._update_channels(channels)
    
    def _on_rc_channels_raw(self, msg):
        """Handle RC_CHANNELS_RAW message."""
        channels = [
            msg.chan1_raw, msg.chan2_raw, msg.chan3_raw, msg.chan4_raw,
            msg.chan5_raw, msg.chan6_raw, msg.chan7_raw, msg.chan8_raw
        ]
        self._update_channels(channels)
    
    def _update_channels(self, channels):
        """Update all channel displays."""
        for i, value in enumerate(channels):
            if i < 8:
                # Clamp value to valid range
                value = max(self.RC_MIN, min(self.RC_MAX, value))
                self.channel_bars[i].setValue(value)
                self.channel_labels[i].setText(str(value))
