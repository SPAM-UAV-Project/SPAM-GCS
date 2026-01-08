"""
General Page - Main view with map, attitude indicator, and telemetry.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSplitter
)
from PyQt5.QtCore import Qt

from src.widgets.map_widget import MapWidget
from src.widgets.attitude_widget import AttitudeWidget
from src.widgets.telemetry_widget import TelemetryWidget


class GeneralPage(QWidget):
    """Main dashboard page with map, attitude, and telemetry displays."""
    
    def __init__(self, message_broker, parent=None):
        super().__init__(parent)
        self.message_broker = message_broker
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Map
        map_frame = QFrame()
        map_frame.setObjectName("statusCard")
        map_layout = QVBoxLayout(map_frame)
        map_layout.setContentsMargins(8, 8, 8, 8)
        
        map_title = QLabel("Map View")
        map_title.setObjectName("sectionTitle")
        map_layout.addWidget(map_title)
        
        self.map_widget = MapWidget(self.message_broker)
        map_layout.addWidget(self.map_widget, 1)
        
        splitter.addWidget(map_frame)
        
        # Right panel - Attitude + Telemetry
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        # Attitude indicator
        attitude_frame = QFrame()
        attitude_frame.setObjectName("statusCard")
        attitude_layout = QVBoxLayout(attitude_frame)
        attitude_layout.setContentsMargins(8, 8, 8, 8)
        
        attitude_title = QLabel("Attitude")
        attitude_title.setObjectName("sectionTitle")
        attitude_layout.addWidget(attitude_title)
        
        self.attitude_widget = AttitudeWidget(self.message_broker)
        attitude_layout.addWidget(self.attitude_widget)
        
        right_layout.addWidget(attitude_frame)
        
        # Telemetry display
        telemetry_frame = QFrame()
        telemetry_frame.setObjectName("statusCard")
        telemetry_layout = QVBoxLayout(telemetry_frame)
        telemetry_layout.setContentsMargins(8, 8, 8, 8)
        
        telemetry_title = QLabel("Telemetry")
        telemetry_title.setObjectName("sectionTitle")
        telemetry_layout.addWidget(telemetry_title)
        
        self.telemetry_widget = TelemetryWidget(self.message_broker)
        telemetry_layout.addWidget(self.telemetry_widget)
        
        right_layout.addWidget(telemetry_frame, 1)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 300])
        
        layout.addWidget(splitter)
    
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'map_widget'):
            self.map_widget.cleanup()
