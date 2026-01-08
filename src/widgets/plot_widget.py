"""
Plot Widget - Configurable real-time plot for MAVLink data.
Includes EULER_ANGLES which converts from quaternion.
"""

import math
from collections import deque
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg


# Available MAVLink messages and their plottable fields
# EULER_ANGLES is a special computed message from quaternion
PLOTTABLE_MESSAGES = {
    'EULER_ANGLES': ['roll_deg', 'pitch_deg', 'yaw_deg', 'roll', 'pitch', 'yaw'],  # Computed from quaternion
    'ATTITUDE': ['roll', 'pitch', 'yaw', 'rollspeed', 'pitchspeed', 'yawspeed'],
    'ATTITUDE_QUATERNION': ['q1', 'q2', 'q3', 'q4', 'rollspeed', 'pitchspeed', 'yawspeed'],
    'LOCAL_POSITION_NED': ['x', 'y', 'z', 'vx', 'vy', 'vz'],
    'GLOBAL_POSITION_INT': ['lat', 'lon', 'alt', 'relative_alt', 'vx', 'vy', 'vz', 'hdg'],
    'SCALED_IMU': ['xacc', 'yacc', 'zacc', 'xgyro', 'ygyro', 'zgyro', 'xmag', 'ymag', 'zmag'],
    'SCALED_IMU2': ['xacc', 'yacc', 'zacc', 'xgyro', 'ygyro', 'zgyro', 'xmag', 'ymag', 'zmag'],
    'RAW_IMU': ['xacc', 'yacc', 'zacc', 'xgyro', 'ygyro', 'zgyro', 'xmag', 'ymag', 'zmag'],
    'HIGHRES_IMU': ['xacc', 'yacc', 'zacc', 'xgyro', 'ygyro', 'zgyro', 'xmag', 'ymag', 'zmag', 'abs_pressure', 'diff_pressure', 'pressure_alt', 'temperature'],
    'RC_CHANNELS': ['chan1_raw', 'chan2_raw', 'chan3_raw', 'chan4_raw', 'chan5_raw', 'chan6_raw', 'chan7_raw', 'chan8_raw'],
    'SERVO_OUTPUT_RAW': ['servo1_raw', 'servo2_raw', 'servo3_raw', 'servo4_raw'],
    'VFR_HUD': ['airspeed', 'groundspeed', 'heading', 'throttle', 'alt', 'climb'],
    'SYS_STATUS': ['voltage_battery', 'current_battery', 'battery_remaining'],
}


def quaternion_to_euler(q0, q1, q2, q3):
    """Convert quaternion to euler angles (roll, pitch, yaw) in radians."""
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
    Allows selection of message type and field to plot.
    Supports EULER_ANGLES computed from quaternion.
    """
    
    BUFFER_SIZE = 500
    
    def __init__(self, message_broker, plot_id=1, parent=None):
        super().__init__(parent)
        self.message_broker = message_broker
        self.plot_id = plot_id
        
        self.data = deque(maxlen=self.BUFFER_SIZE)
        self.time_data = deque(maxlen=self.BUFFER_SIZE)
        self.sample_count = 0
        
        self.current_message = None
        self.current_field = None
        self._euler_subscribed = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        header = QHBoxLayout()
        header.setSpacing(4)
        
        self.message_combo = QComboBox()
        self.message_combo.setMaximumWidth(140)
        self.message_combo.addItem("-- Select --")
        self.message_combo.addItems(sorted(PLOTTABLE_MESSAGES.keys()))
        self.message_combo.currentTextChanged.connect(self._on_message_changed)
        header.addWidget(self.message_combo)
        
        self.field_combo = QComboBox()
        self.field_combo.setMaximumWidth(100)
        self.field_combo.setEnabled(False)
        self.field_combo.currentTextChanged.connect(self._on_field_changed)
        header.addWidget(self.field_combo)
        
        header.addStretch()
        layout.addLayout(header)
        
        pg.setConfigOptions(antialias=True)
        
        self.plot = pg.PlotWidget()
        self.plot.setBackground('#252540')
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.getAxis('left').setPen('#888')
        self.plot.getAxis('bottom').setPen('#888')
        self.plot.getAxis('left').setTextPen('#888')
        self.plot.getAxis('bottom').setTextPen('#888')
        
        self.curve = self.plot.plot(pen=pg.mkPen('#6c63ff', width=2))
        
        layout.addWidget(self.plot)
    
    def _on_message_changed(self, message_type):
        """Handle message type selection."""
        # Unsubscribe from previous message
        if self.current_message:
            if self.current_message == 'EULER_ANGLES':
                self.message_broker.unsubscribe('ATTITUDE_QUATERNION', self._on_quaternion_data)
            else:
                self.message_broker.unsubscribe(self.current_message, self._on_data)
        
        self._euler_subscribed = False
        
        # Clear data
        self.data.clear()
        self.time_data.clear()
        self.sample_count = 0
        self.curve.setData([], [])
        
        self.field_combo.clear()
        
        if message_type in PLOTTABLE_MESSAGES:
            fields = PLOTTABLE_MESSAGES[message_type]
            self.field_combo.addItems(fields)
            self.field_combo.setEnabled(True)
            self.current_message = message_type
            
            # Subscribe based on message type
            if message_type == 'EULER_ANGLES':
                self.message_broker.subscribe('ATTITUDE_QUATERNION', self._on_quaternion_data)
                self._euler_subscribed = True
            else:
                self.message_broker.subscribe(message_type, self._on_data)
        else:
            self.field_combo.setEnabled(False)
            self.current_message = None
            self.current_field = None
    
    def _on_field_changed(self, field):
        """Handle field selection."""
        self.current_field = field
        self.data.clear()
        self.time_data.clear()
        self.sample_count = 0
        self.curve.setData([], [])
    
    def _on_quaternion_data(self, msg):
        """Handle quaternion data and convert to euler."""
        if not self.current_field or self.current_message != 'EULER_ANGLES':
            return
        
        try:
            roll, pitch, yaw = quaternion_to_euler(msg.q1, msg.q2, msg.q3, msg.q4)
            
            euler_data = {
                'roll': roll,
                'pitch': pitch,
                'yaw': yaw,
                'roll_deg': math.degrees(roll),
                'pitch_deg': math.degrees(pitch),
                'yaw_deg': math.degrees(yaw)
            }
            
            value = euler_data.get(self.current_field)
            if value is not None:
                self.data.append(value)
                self.time_data.append(self.sample_count)
                self.sample_count += 1
                self.curve.setData(list(self.time_data), list(self.data))
                
        except Exception:
            pass
    
    def _on_data(self, msg):
        """Handle incoming MAVLink data."""
        if not self.current_field:
            return
        
        try:
            value = getattr(msg, self.current_field)
            
            # Handle special scaling for certain fields
            if self.current_message == 'GLOBAL_POSITION_INT':
                if self.current_field in ['lat', 'lon']:
                    value = value / 1e7
                elif self.current_field in ['alt', 'relative_alt']:
                    value = value / 1000.0
                elif self.current_field == 'hdg':
                    value = value / 100.0
            
            self.data.append(value)
            self.time_data.append(self.sample_count)
            self.sample_count += 1
            
            self.curve.setData(list(self.time_data), list(self.data))
            
        except AttributeError:
            pass
