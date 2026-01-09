"""
Plot Widget - Configurable real-time plot for MAVLink data.
Includes EULER_ANGLES which converts from quaternion.
"""

import math
import time
import threading
from collections import deque
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel
)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg


# Available MAVLink messages and their plottable fields
# Tailored to user's custom FC
PLOTTABLE_MESSAGES = {
    'ATTITUDE_QUATERNION': ['q1', 'q2', 'q3', 'q4', 'rollspeed', 'pitchspeed', 'yawspeed', 
                           'roll_deg', 'pitch_deg', 'yaw_deg', 'roll', 'pitch', 'yaw'],
    'SET_ATTITUDE_TARGET': ['body_roll_rate', 'body_pitch_rate', 'body_yaw_rate', 'thrust',
                           'roll_deg', 'pitch_deg', 'yaw_deg', 'roll', 'pitch', 'yaw'],
    'LOCAL_POSITION_NED': ['x', 'y', 'z', 'vx', 'vy', 'vz'],
    'HIGHRES_IMU': ['xacc', 'yacc', 'zacc', 'xgyro', 'ygyro', 'zgyro'],
    'RC_CHANNELS': ['chan1_raw', 'chan2_raw', 'chan3_raw', 'chan4_raw', 'chan5_raw', 'chan6_raw'],
    'SYS_STATUS': ['voltage_battery', 'current_battery', 'battery_remaining'],
}


def quaternion_to_euler(q0, q1, q2, q3):
    sinr_cosp = 2.0 * (q0 * q1 + q2 * q3)
    cosr_cosp = 1.0 - 2.0 * (q1 * q1 + q2 * q2)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    
    sinp = 2.0 * (q0 * q2 - q3 * q1)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)
    else:
        pitch = math.asin(sinp)
    
    siny_cosp = 2.0 * (q0 * q3 + q1 * q2)
    cosy_cosp = 1.0 - 2.0 * (q2 * q2 + q3 * q3)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    
    return roll, pitch, yaw


class PlotWidget(QWidget):
    """
    Configurable real-time plot widget.
    """
    
    def __init__(self, message_broker, plot_id=1, parent=None):
        super().__init__(parent)
        self.message_broker = message_broker
        self.plot_id = plot_id
        
        self.data_lock = threading.Lock()
        
        # Buffer optimization: 1500 points (30s @ 50Hz)
        # Prevents list conversion lag after long runtimes
        self.max_buffer_size = 1500 
        self.data = deque(maxlen=self.max_buffer_size)
        self.time_data = deque(maxlen=self.max_buffer_size)
        self.start_time = time.time()
        
        self.current_message = None
        self.current_field = None
        
        self.time_window = 5.0  # Default 5s window
        
        # Update at 50Hz (20ms) as requested
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._render_plot)
        self.update_timer.start(20)
        self._pending_update = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        header = QHBoxLayout()
        header.setSpacing(8)
        
        # Topic Selector
        self.message_combo = QComboBox()
        self.message_combo.setMaximumWidth(140)
        self.message_combo.addItem("-- Select --")
        self.message_combo.addItems(sorted(PLOTTABLE_MESSAGES.keys()))
        self.message_combo.currentTextChanged.connect(self._on_message_changed)
        header.addWidget(self.message_combo)
        
        # Field Selector
        self.field_combo = QComboBox()
        self.field_combo.setMaximumWidth(100)
        self.field_combo.setEnabled(False)
        self.field_combo.currentTextChanged.connect(self._on_field_changed)
        header.addWidget(self.field_combo)
        
        # Time Selector
        time_label = QLabel("T:")
        time_label.setStyleSheet("color: #888; font-weight: bold;")
        header.addWidget(time_label)
        
        self.time_combo = QComboBox()
        self.time_combo.setMaximumWidth(60)
        self.time_combo.addItems(["2s", "5s", "10s", "30s"])
        self.time_combo.setCurrentText("5s")
        self.time_combo.currentTextChanged.connect(self._on_time_changed)
        header.addWidget(self.time_combo)
        
        header.addStretch()
        layout.addLayout(header)
        
        pg.setConfigOptions(antialias=True)
        
        self.plot = pg.PlotWidget()
        self.plot.setBackground('#252540')
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.getAxis('left').setPen('#888')
        self.plot.getAxis('bottom').setPen('#888')
        
        # Ensure Y-axis always autofits
        self.plot.enableAutoRange(axis='y', enable=True)
        self.plot.setAutoVisible(y=True)
        
        self.curve = self.plot.plot(pen=pg.mkPen('#6c63ff', width=2))
        
        layout.addWidget(self.plot)
        
    def _on_time_changed(self, text):
        try:
            val = int(text.replace('s', ''))
            self.time_window = float(val)
        except ValueError:
            pass
    
    def _on_message_changed(self, message_type):
        if self.current_message:
            self.message_broker.unsubscribe(self.current_message, self._on_message_received)
        
        self._clear_data()
        self.field_combo.clear()
        
        if message_type in PLOTTABLE_MESSAGES:
            fields = PLOTTABLE_MESSAGES[message_type]
            self.field_combo.blockSignals(True)
            self.field_combo.addItems(fields)
            self.field_combo.setEnabled(True)
            self.field_combo.blockSignals(False)
            
            self.current_message = message_type
            self.message_broker.subscribe(message_type, self._on_message_received)
                
            if fields:
               self.field_combo.setCurrentIndex(0)
               self.current_field = fields[0]
        else:
            self.field_combo.setEnabled(False)
            self.current_message = None
            self.current_field = None
            
    def _on_field_changed(self, field_name):
        self.current_field = field_name
        self._clear_data()

    def _clear_data(self):
        with self.data_lock:
            self.data.clear()
            self.time_data.clear()
            self.curve.setData([], [])

    def _on_message_received(self, msg):
        """Unified handler for all messages, including derived fields"""
        if not self.current_field:
            return
            
        val = None
        
        # Check if we need to derive Euler angles
        if self.current_field in ['roll', 'pitch', 'yaw', 'roll_deg', 'pitch_deg', 'yaw_deg']:
            try:
                q = None
                # Check for ATTITUDE_QUATERNION format (q1, q2, q3, q4)
                if hasattr(msg, 'q1'):
                    q = [msg.q1, msg.q2, msg.q3, msg.q4]
                # Check for SET_ATTITUDE_TARGET format (q array)
                elif hasattr(msg, 'q') and len(msg.q) >= 4:
                    q = msg.q
                
                if q:
                    r, p, y = quaternion_to_euler(q[0], q[1], q[2], q[3])
                    
                    if self.current_field == 'roll': val = r
                    elif self.current_field == 'pitch': val = p
                    elif self.current_field == 'yaw': val = y
                    elif self.current_field == 'roll_deg': val = math.degrees(r)
                    elif self.current_field == 'pitch_deg': val = math.degrees(p)
                    elif self.current_field == 'yaw_deg': val = math.degrees(y)
            except Exception:
                pass
        
        # If not derived (or derivation failed), try direct attribute access
        if val is None:
            try:
                val = getattr(msg, self.current_field)
            except AttributeError:
                pass
        
        if val is not None:
            self._buffer_data(val)

    def _buffer_data(self, value):
        t = time.time() - self.start_time
        with self.data_lock:
            self.time_data.append(t)
            self.data.append(value)
            self._pending_update = True
        
    def _render_plot(self):
        if self._pending_update and self.isVisible():
            with self.data_lock:
                if len(self.time_data) > 0:
                    t_current = self.time_data[-1]
                    t_min = t_current - self.time_window
                    
                    self.plot.setXRange(t_min, t_current, padding=0)
                    self.curve.setData(list(self.time_data), list(self.data))
                    
                    self._pending_update = False
