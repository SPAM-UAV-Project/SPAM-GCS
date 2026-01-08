"""
Telemetry Widget - Modern tile-based display of live telemetry data.
"""

import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame
)
from PyQt5.QtCore import Qt


class TelemetryTile(QFrame):
    """Individual telemetry tile with label and value."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("telemetryTile")
        self.setStyleSheet("""
            #telemetryTile {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 60, 90, 0.6),
                    stop:1 rgba(40, 40, 70, 0.4));
                border: 1px solid rgba(100, 100, 140, 0.3);
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        
        # Title
        title_label = QLabel(title.upper())
        title_label.setStyleSheet(
            "color: rgba(160, 160, 200, 0.8); font-size: 9px; font-weight: 600; letter-spacing: 1px; background: transparent; border: none;"
        )
        layout.addWidget(title_label)
        
        # Value
        self.value_label = QLabel("---")
        self.value_label.setStyleSheet(
            "color: #ffffff; font-size: 13px; font-family: 'Segoe UI', 'Consolas', monospace; font-weight: 500; background: transparent; border: none;"
        )
        layout.addWidget(self.value_label)
    
    def set_value(self, value: str):
        """Update the displayed value."""
        self.value_label.setText(value)
    
    def set_color(self, color: str):
        """Set the value text color."""
        self.value_label.setStyleSheet(
            f"color: {color}; font-size: 13px; font-family: 'Segoe UI', 'Consolas', monospace; font-weight: 500; background: transparent; border: none;"
        )


class TelemetryWidget(QWidget):
    """Modern tile-based telemetry display."""
    
    def __init__(self, message_broker, parent=None):
        super().__init__(parent)
        self.message_broker = message_broker
        self.tiles = {}
        self._setup_ui()
        self._subscribe_to_messages()
    
    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Define tiles: (key, title, row, col, colspan)
        tile_config = [
            ("position", "Position NED", 0, 0, 1),
            ("velocity", "Velocity NED", 0, 1, 1),
            ("altitude", "Altitude", 1, 0, 1),
            ("heading", "Heading", 1, 1, 1),
            ("battery", "Battery", 2, 0, 1),
            ("status", "System", 2, 1, 1),
        ]
        
        for key, title, row, col, colspan in tile_config:
            tile = TelemetryTile(title)
            self.tiles[key] = tile
            layout.addWidget(tile, row, col, 1, colspan)
    
    def _subscribe_to_messages(self):
        """Subscribe to relevant MAVLink messages."""
        self.message_broker.subscribe('LOCAL_POSITION_NED', self._on_local_position)
        self.message_broker.subscribe('GLOBAL_POSITION_INT', self._on_global_position)
        self.message_broker.subscribe('SYS_STATUS', self._on_sys_status)
        self.message_broker.subscribe('VFR_HUD', self._on_vfr_hud)
        self.message_broker.subscribe('HEARTBEAT', self._on_heartbeat)
    
    def _on_local_position(self, msg):
        """Handle LOCAL_POSITION_NED message."""
        self.tiles['position'].set_value(
            f"N:{msg.x:+.1f}  E:{msg.y:+.1f}  D:{msg.z:+.1f} m"
        )
        self.tiles['velocity'].set_value(
            f"{msg.vx:+.1f}  {msg.vy:+.1f}  {msg.vz:+.1f} m/s"
        )
        self.tiles['altitude'].set_value(f"{-msg.z:.1f} m")
    
    def _on_global_position(self, msg):
        """Handle GLOBAL_POSITION_INT message."""
        if hasattr(msg, 'hdg') and msg.hdg != 65535:
            hdg = msg.hdg / 100.0
            self.tiles['heading'].set_value(f"{hdg:.0f}°")
    
    def _on_sys_status(self, msg):
        """Handle SYS_STATUS message."""
        voltage = msg.voltage_battery / 1000.0 if msg.voltage_battery != 65535 else 0
        current = msg.current_battery / 100.0 if msg.current_battery != -1 else 0
        
        if voltage > 0:
            text = f"{voltage:.2f}V"
            if current > 0:
                text += f"  {current:.1f}A"
            self.tiles['battery'].set_value(text)
            
            if voltage > 11.5:
                self.tiles['battery'].set_color("#4ade80")
            elif voltage > 10.5:
                self.tiles['battery'].set_color("#fbbf24")
            else:
                self.tiles['battery'].set_color("#f87171")
    
    def _on_vfr_hud(self, msg):
        """Handle VFR_HUD message."""
        self.tiles['heading'].set_value(f"{msg.heading}°")
    
    def _on_heartbeat(self, msg):
        """Handle HEARTBEAT message."""
        status_map = {
            0: ("Uninit", "#888"),
            1: ("Boot", "#fbbf24"),
            2: ("Calibrating", "#fbbf24"),
            3: ("Standby", "#4ade80"),
            4: ("Active", "#4ade80"),
            5: ("Critical", "#f87171"),
            6: ("Emergency", "#f87171"),
            7: ("Poweroff", "#888"),
            8: ("Terminating", "#f87171")
        }
        
        status_name, color = status_map.get(msg.system_status, ("Unknown", "#888"))
        self.tiles['status'].set_value(f"{status_name}  Mode:{msg.custom_mode}")
        self.tiles['status'].set_color(color)
