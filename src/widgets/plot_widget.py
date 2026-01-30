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
    'NAMED_VALUE_FLOAT': ['enc_angle'],  # MAVLink truncates names to 10 chars
    'DEBUG_FLOAT_ARRAY': ['motor_f_0', 'motor_f_1', 'motor_f_2', 'motor_f_3']
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
        
        # Rate tracking for Hz display
        self._msg_count = 0
        self._last_rate_time = time.time()
        self._current_hz = 0.0
        
        # Update at 50Hz (20ms) as requested
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._render_plot)
        self.update_timer.start(20)
        self._pending_update = False
        
        # Last received values for display
        self.last_msg_name = ""
        self.last_array_values = []
        self.last_single_value = 0.0
        
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
        
        # Hz display
        self.hz_label = QLabel("-- Hz")
        self.hz_label.setStyleSheet("color: #6c63ff; font-weight: bold; font-size: 11px;")
        self.hz_label.setMinimumWidth(50)
        header.addWidget(self.hz_label)
        
        layout.addLayout(header)
        
        pg.setConfigOptions(antialias=True)
        
        self.plot = pg.PlotWidget()
        self.plot.setBackground('#252540')
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.getAxis('left').setPen('#888')
        self.plot.getAxis('bottom').setPen('#888')
        
        # Optimization: Only render what's visible
        self.plot.getPlotItem().setClipToView(True)
        
        # Ensure Y-axis always autofits
        self.plot.enableAutoRange(axis='y', enable=True)
        self.plot.setAutoVisible(y=True)
        
        self.curve = self.plot.plot(pen=pg.mkPen('#6c63ff', width=2))
        
        # Overlay for current value(s)
        self.value_label = QLabel(self.plot)
        self.value_label.setStyleSheet("""
            background-color: rgba(37, 37, 64, 0.7);
            color: #4ade80;
            font-weight: bold;
            font-size: 13px;
            padding: 4px;
            border-radius: 4px;
        """)
        self.value_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.value_label.move(10, 40)  # Below header
        self.value_label.hide()
        
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
            self.last_array_values = []
            self.last_single_value = 0.0
            self.value_label.hide()

    def _on_message_received(self, msg):
        """Unified handler for all messages, including derived fields"""
        if not self.current_field:
            return
            
        val = None
        
        # Handle NAMED_VALUE_FLOAT messages (match by name field)
        if self.current_message == 'NAMED_VALUE_FLOAT':
            try:
                if hasattr(msg, 'name') and hasattr(msg, 'value'):
                    # Decode name (may be bytes) and normalize
                    # MAVLink stores names as fixed 10-char array padded with nulls/spaces
                    msg_name = msg.name
                    if isinstance(msg_name, bytes):
                        msg_name = msg_name.decode('ascii', errors='ignore')
                    # Strip null terminators, spaces, and any other padding
                    msg_name = msg_name.rstrip('\x00').strip()
                    
                    # Debug: uncomment to see what names are being received
                    # print(f"NAMED_VALUE_FLOAT: name='{msg_name}', looking for='{self.current_field}', value={msg.value}")
                    
                    # Check if this is the named value we're plotting
                    if msg_name == self.current_field:
                        val = msg.value
            except Exception as e:
                print(f"NAMED_VALUE_FLOAT parse error: {e}")

        # Handle DEBUG_FLOAT_ARRAY messages
        elif self.current_message == 'DEBUG_FLOAT_ARRAY':
            try:
                msg_name = msg.name
                if isinstance(msg_name, bytes):
                    msg_name = msg_name.decode('ascii', errors='ignore')
                msg_name = msg_name.rstrip('\x00').strip()
                self.last_msg_name = msg_name

                if msg_name == "motor_f":
                    self.last_array_values = list(msg.data[:4])
                    # Extract index from field name motor_f_N
                    try:
                        idx = int(self.current_field.split('_')[-1])
                        val = self.last_array_values[idx]
                    except (ValueError, IndexError):
                        pass
                else:
                    # Generic handling for other debug arrays
                    # For now just plot if field matches index
                    pass
            except Exception as e:
                print(f"DEBUG_FLOAT_ARRAY parse error: {e}")

        
        # Check if we need to derive Euler angles
        elif self.current_field in ['roll', 'pitch', 'yaw', 'roll_deg', 'pitch_deg', 'yaw_deg']:
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
            self.last_single_value = val
            self._buffer_data(val)

    def _buffer_data(self, value):
        t = time.time() - self.start_time
        with self.data_lock:
            self.time_data.append(t)
            self.data.append(value)
            self._pending_update = True
            
            # Track message rate
            self._msg_count += 1
        
    def _render_plot(self):
        # Calculate Hz every render (50Hz timer)
        now = time.time()
        elapsed = now - self._last_rate_time
        if elapsed >= 0.5:  # Update Hz display every 0.5s
            self._current_hz = self._msg_count / elapsed
            self._msg_count = 0
            self._last_rate_time = now
            self.hz_label.setText(f"{self._current_hz:.0f} Hz")
        
        if self._pending_update and self.isVisible():
            with self.data_lock:
                if len(self.time_data) > 0:
                    t_current = self.time_data[-1]
                    t_min = t_current - self.time_window
                    
                    self.plot.setXRange(t_min, t_current, padding=0)
                    
                    # Optimization: skip finite check for speed
                    self.curve.setData(list(self.time_data), list(self.data), skipFiniteCheck=True)
                    
                    # Update value display
                    if self.current_message == 'DEBUG_FLOAT_ARRAY' and self.last_msg_name == "motor_f" and self.last_array_values:
                        vals_str = ", ".join([f"{v:.2f}" for v in self.last_array_values])
                        self.value_label.setText(f"M: [{vals_str}]")
                        self.value_label.show()
                        self.value_label.adjustSize()
                    elif self.last_single_value is not None:
                        self.value_label.setText(f"Val: {self.last_single_value:.2f}")
                        self.value_label.show()
                        self.value_label.adjustSize()
                    else:
                        self.value_label.hide()
                    
                    self._pending_update = False
