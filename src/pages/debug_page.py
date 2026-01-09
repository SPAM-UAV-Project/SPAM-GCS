"""
Debug Page - System identification and tuning dashboard.
"""

import time
import math
import threading
from collections import deque
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QComboBox, QFrame
)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg

from src.widgets.rc_widget import RCWidget
from src.widgets.plot_widget import PlotWidget, quaternion_to_euler

class PidPlotWidget(QFrame):
    """
    Specialized plot for comparing Target vs Actual values.
    Uses buffered rendering to prevent UI freeze.
    """
    def __init__(self, title, unit="", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e2f;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("color: #888; font-weight: bold; font-size: 11px;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Legend/Values
        self.value_label = QLabel(f"T: 0.00  A: 0.00 {unit}")
        self.value_label.setStyleSheet("color: #ddd; font-family: Consolas; font-weight: bold;")
        header_layout.addWidget(self.value_label)
        
        layout.addLayout(header_layout)
        
        # Plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1e1e2f')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.getAxis('left').setPen('#666')
        self.plot_widget.getAxis('bottom').setPen('#666')
        self.plot_widget.setStyleSheet("border: none;")
        
        # Ensure Y-axis always autofits
        self.plot_widget.enableAutoRange(axis='y', enable=True)
        self.plot_widget.setAutoVisible(y=True)
        
        layout.addWidget(self.plot_widget)
        
        # Buffer config
        # Optimized for 50Hz data stream
        self.max_buffer = 1500 
        self.times = deque(maxlen=self.max_buffer)
        self.target_data = deque(maxlen=self.max_buffer)
        self.actual_data = deque(maxlen=self.max_buffer)
        
        self.data_lock = threading.Lock()
        
        self.target_curve = self.plot_widget.plot(pen=pg.mkPen('#6c63ff', width=2), name='Target')
        self.actual_curve = self.plot_widget.plot(pen=pg.mkPen('#4ade80', width=2), name='Actual')
        
        self.start_time = time.time()
        self.time_window = 5.0 # Default 5s
        
        # Timer for 50Hz rendering
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._render)
        self.update_timer.start(20)
        self._pending_update = False
        
        self.last_target = 0
        self.last_actual = 0
        
    def add_data(self, target, actual):
        t = time.time() - self.start_time
        
        with self.data_lock:
            self.times.append(t)
            self.target_data.append(target)
            self.actual_data.append(actual)
            
            self.last_target = target
            self.last_actual = actual
            self._pending_update = True
        
    def _render(self):
        if self._pending_update and self.isVisible():
            with self.data_lock:
                if len(self.times) > 0:
                    # Update values
                    self.value_label.setText(f"T: {self.last_target:6.2f}  A: {self.last_actual:6.2f}")
                    
                    # Set X Range based on time window
                    t_current = self.times[-1]
                    t_min = t_current - self.time_window
                    self.plot_widget.setXRange(t_min, t_current, padding=0)
                    
                    self.target_curve.setData(list(self.times), list(self.target_data))
                    self.actual_curve.setData(list(self.times), list(self.actual_data))
                    
                    self._pending_update = False
        
    def set_time_window(self, seconds):
        self.time_window = seconds


class DebugPage(QWidget):
    """
    Debug dashboard with linked PID plots for tuning.
    """
    
    def __init__(self, message_broker, parent=None):
        super().__init__(parent)
        self.message_broker = message_broker
        
        self.current_axis = 'roll' 
        self.target_att_euler = [0, 0, 0]
        self.actual_att_euler = [0, 0, 0]
        self.target_rate = [0, 0, 0]
        self.actual_rate = [0, 0, 0]
        
        self._setup_ui()
        self._subscribe_to_messages()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Controls
        controls = QHBoxLayout()
        controls.setSpacing(16)
        
        controls.addWidget(QLabel("AXIS:"))
        self.axis_combo = QComboBox()
        self.axis_combo.addItems(["ROLL", "PITCH", "YAW"])
        self.axis_combo.currentIndexChanged.connect(self._on_axis_changed)
        controls.addWidget(self.axis_combo)
        
        controls.addWidget(QLabel("WINDOW:"))
        self.window_combo = QComboBox()
        self.window_combo.addItems(["2s", "5s", "10s", "30s"])
        self.window_combo.setCurrentText("5s")
        self.window_combo.currentTextChanged.connect(self._on_window_changed)
        controls.addWidget(self.window_combo)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Grid
        grid = QGridLayout()
        grid.setSpacing(16)
        
        self.att_plot = PidPlotWidget("ATTITUDE RESPONSE", "deg")
        grid.addWidget(self.att_plot, 0, 0)
        
        self.rc_widget = RCWidget(self.message_broker)
        grid.addWidget(self.rc_widget, 0, 1)
        
        self.rate_plot = PidPlotWidget("RATE RESPONSE", "deg/s")
        grid.addWidget(self.rate_plot, 1, 0)
        
        self.extra_plot = PlotWidget(self.message_broker)
        # Force default time window on extra plot to match
        self.extra_plot.time_window = 5.0
        self.extra_plot.time_combo.setCurrentText("5s")
        
        self.extra_plot.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                border-radius: 8px;
            }
        """)
        grid.addWidget(self.extra_plot, 1, 1)
        
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 1)
        
        layout.addLayout(grid)
        
    def _subscribe_to_messages(self):
        # User sends SET_ATTITUDE_TARGET (#82) not ATTITUDE_TARGET (#83)
        self.message_broker.subscribe('SET_ATTITUDE_TARGET', self._on_set_attitude_target)
        self.message_broker.subscribe('ATTITUDE_QUATERNION', self._on_attitude_quaternion)
        self.message_broker.subscribe('HIGHRES_IMU', self._on_highres_imu)
    
    def _on_highres_imu(self, msg):
        scale = 180.0 / math.pi
        self.actual_rate = [
            msg.xgyro * scale,
            msg.ygyro * scale,
            msg.zgyro * scale
        ]
        self._update_plots()
        
    def _on_attitude_quaternion(self, msg):
        r, p, y = quaternion_to_euler(msg.q1, msg.q2, msg.q3, msg.q4)
        self.actual_att_euler = [math.degrees(r), math.degrees(p), math.degrees(y)]
        self._update_plots()
        
    def _on_set_attitude_target(self, msg):
        # msg.q is a list of 4 floats [w, x, y, z]
        r, p, y = quaternion_to_euler(msg.q[0], msg.q[1], msg.q[2], msg.q[3])
        self.target_att_euler = [math.degrees(r), math.degrees(p), math.degrees(y)]
        self.target_rate = [
            math.degrees(msg.body_roll_rate),
            math.degrees(msg.body_pitch_rate),
            math.degrees(msg.body_yaw_rate)
        ]
        self._update_plots()
        
    def _on_axis_changed(self, index):
        modes = ['roll', 'pitch', 'yaw']
        self.current_axis = modes[index]
        
    def _on_window_changed(self, text):
        seconds = int(text.replace('s', ''))
        self.att_plot.set_time_window(seconds)
        self.rate_plot.set_time_window(seconds)
        
    def _update_plots(self):
        idx = 0 if self.current_axis == 'roll' else (1 if self.current_axis == 'pitch' else 2)
        self.att_plot.add_data(self.target_att_euler[idx], self.actual_att_euler[idx])
        self.rate_plot.add_data(self.target_rate[idx], self.actual_rate[idx])
