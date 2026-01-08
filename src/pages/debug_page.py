"""
Debug Page - Real-time plots and RC input display.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt

from src.widgets.plot_widget import PlotWidget
from src.widgets.rc_widget import RCWidget


class DebugPage(QWidget):
    """Debug page with configurable plots and RC channel display."""
    
    def __init__(self, message_broker, parent=None):
        super().__init__(parent)
        self.message_broker = message_broker
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Plots area (2x2 grid)
        plots_frame = QFrame()
        plots_frame.setObjectName("statusCard")
        plots_layout = QVBoxLayout(plots_frame)
        plots_layout.setContentsMargins(8, 8, 8, 8)
        
        plots_title = QLabel("Data Plots")
        plots_title.setObjectName("sectionTitle")
        plots_layout.addWidget(plots_title)
        
        # Grid for 4 plots
        plot_grid = QGridLayout()
        plot_grid.setSpacing(8)
        
        self.plots = []
        for i in range(4):
            plot = PlotWidget(self.message_broker, plot_id=i+1)
            self.plots.append(plot)
            row, col = divmod(i, 2)
            plot_grid.addWidget(plot, row, col)
        
        plots_layout.addLayout(plot_grid)
        layout.addWidget(plots_frame, 1)
        
        # RC channels panel (compact)
        rc_frame = QFrame()
        rc_frame.setObjectName("statusCard")
        rc_frame.setFixedWidth(120)
        rc_layout = QVBoxLayout(rc_frame)
        rc_layout.setContentsMargins(4, 8, 4, 8)
        
        self.rc_widget = RCWidget(self.message_broker)
        rc_layout.addWidget(self.rc_widget)
        
        layout.addWidget(rc_frame)
