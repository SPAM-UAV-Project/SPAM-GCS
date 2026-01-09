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
from src.widgets.plot_widget import PlotWidget


class GeneralPage(QWidget):
    """Main dashboard page with map, attitude, and telemetry displays."""
    
    def __init__(self, message_broker, parent=None):
        super().__init__(parent)
        self.message_broker = message_broker
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(12)  # Wider handle for visual separation
        
        # Left panel - Map
        map_container = QWidget()
        map_layout = QVBoxLayout(map_container)
        map_layout.setContentsMargins(0, 0, 8, 0)  # Add right margin to separate from handle
        map_layout.setSpacing(8)
        
        # Minimalist header
        map_header = QLabel("MAP VIEW")
        map_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #666; letter-spacing: 1px;")
        map_layout.addWidget(map_header)
        
        self.map_widget = MapWidget(self.message_broker)
        # Add subtle radius to map and clip
        self.map_widget.setStyleSheet("border-radius: 12px;")
        map_layout.addWidget(self.map_widget, 1)
        
        splitter.addWidget(map_container)
        
        # Right panel - Attitude + Telemetry + Graph
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)  # Add left margin
        right_layout.setSpacing(16)
        
        # 1. Attitude (Top)
        attitude_container = QWidget()
        attitude_layout = QVBoxLayout(attitude_container)
        attitude_layout.setContentsMargins(0, 0, 0, 0)
        attitude_layout.setSpacing(8)
        
        attitude_header = QLabel("ATTITUDE")
        attitude_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #666; letter-spacing: 1px;")
        attitude_layout.addWidget(attitude_header)
        
        self.attitude_widget = AttitudeWidget(self.message_broker)
        attitude_layout.addWidget(self.attitude_widget)
        right_layout.addWidget(attitude_container)
        
        # 2. Telemetry (Middle)
        telemetry_container = QWidget()
        telemetry_layout = QVBoxLayout(telemetry_container)
        telemetry_layout.setContentsMargins(0, 0, 0, 0)
        telemetry_layout.setSpacing(8)
        
        telemetry_header = QLabel("TELEMETRY")
        telemetry_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #666; letter-spacing: 1px;")
        telemetry_layout.addWidget(telemetry_header)
        
        self.telemetry_widget = TelemetryWidget(self.message_broker)
        telemetry_layout.addWidget(self.telemetry_widget)
        right_layout.addWidget(telemetry_container)
        
        # 3. Graph (Bottom)
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(8)
        
        plot_header = QLabel("LIVE PLOT")
        plot_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #666; letter-spacing: 1px;")
        plot_layout.addWidget(plot_header)
        
        self.plot_widget = PlotWidget(self.message_broker)
        # Style it to blend in
        self.plot_widget.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                border-radius: 12px;
            }
        """)
        
        # Default plot settings
        self.plot_widget.time_window = 10.0
        self.plot_widget.time_combo.setCurrentText("10s")
        
        plot_layout.addWidget(self.plot_widget)
        right_layout.addWidget(plot_container, 1) # Give plot expanding space
        
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 360])
        
        # Collapse handle completely to use margins for spacing
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;
            }
        """)
        
        layout.addWidget(splitter)
    
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'map_widget'):
            self.map_widget.cleanup()
