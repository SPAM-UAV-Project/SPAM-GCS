"""
MAVLink Connection Manager.
Handles USB (serial) and WiFi (UDP) connections to the drone.
Uses QThread for proper Qt signal handling and non-blocking operation.
"""

import time
import math
from enum import Enum
from typing import Optional

from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer, QMutex
from pymavlink import mavutil


class ConnectionType(Enum):
    USB = "usb"
    WIFI = "wifi"


class ConnectionWorker(QThread):
    """Background worker thread for MAVLink communication."""
    
    message_received = pyqtSignal(object)
    connection_status_changed = pyqtSignal(bool)
    heartbeat_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    connection_ready = pyqtSignal(bool, str)
    euler_angles = pyqtSignal(dict)  # Converted from quaternion
    
    def __init__(self, connection_string: str, is_serial: bool = True, baudrate: int = 115200):
        super().__init__()
        self.connection_string = connection_string
        self.is_serial = is_serial
        self.baudrate = baudrate
        self._running = False
        self._connected = False
        self._connection = None
        self._last_heartbeat_time = 0
        self._heartbeat_timeout = 3.0
        self._stop_requested = False
    
    def run(self):
        """Main thread loop."""
        self._running = True
        self._stop_requested = False
        
        # Try to establish connection
        try:
            if self.is_serial:
                self._connection = mavutil.mavlink_connection(
                    self.connection_string,
                    baud=self.baudrate,
                    source_system=255,
                    source_component=0
                )
            else:
                self._connection = mavutil.mavlink_connection(
                    self.connection_string,
                    source_system=255,
                    source_component=0
                )
            
            self.connection_ready.emit(True, f"Connected to {self.connection_string}")
            
        except Exception as e:
            self.connection_ready.emit(False, f"Connection failed: {str(e)}")
            self._running = False
            return
        
        # Main receive loop
        while self._running and not self._stop_requested:
            try:
                # Use a small timeout to keep checking stop_requested
                msg = self._connection.recv_match(blocking=True, timeout=0.05)
                
                if self._stop_requested:
                    break
                
                if msg:
                    msg_type = msg.get_type()
                    
                    # Handle heartbeat specially
                    if msg_type == 'HEARTBEAT':
                        self._last_heartbeat_time = time.time()
                        
                        if not self._connected:
                            self._connected = True
                            self.connection_status_changed.emit(True)
                        
                        heartbeat_data = {
                            'type': msg.type,
                            'autopilot': msg.autopilot,
                            'base_mode': msg.base_mode,
                            'custom_mode': msg.custom_mode,
                            'system_status': msg.system_status,
                            'mavlink_version': msg.mavlink_version
                        }
                        self.heartbeat_received.emit(heartbeat_data)
                    
                    # Convert quaternion to euler angles
                    if msg_type == 'ATTITUDE_QUATERNION':
                        euler = self._quaternion_to_euler(msg.q1, msg.q2, msg.q3, msg.q4)
                        self.euler_angles.emit({
                            'roll': euler[0],
                            'pitch': euler[1],
                            'yaw': euler[2],
                            'roll_deg': math.degrees(euler[0]),
                            'pitch_deg': math.degrees(euler[1]),
                            'yaw_deg': math.degrees(euler[2])
                        })
                    
                    # Emit EVERYTHING. No throttling.
                    # Qt signals queue up, so efficient main thread handling is key.
                    # For typical telemetry links (50-200Hz), this is fine.
                    self.message_received.emit(msg)
                
                # Check for heartbeat timeout
                if self._connected and (time.time() - self._last_heartbeat_time) > self._heartbeat_timeout:
                    self._connected = False
                    self.connection_status_changed.emit(False)
                    
            except Exception as e:
                if self._running and not self._stop_requested:
                    time.sleep(0.01)
        
        # Cleanup - CRITICAL: properly close the connection
        self._cleanup()
    
    def _cleanup(self):
        """Clean up connection resources."""
        if self._connection:
            try:
                self._connection.close()
            except:
                pass
            self._connection = None
    
    def _quaternion_to_euler(self, q0, q1, q2, q3):
        """Convert quaternion to euler angles."""
        # Roll
        sinr_cosp = 2.0 * (q0 * q1 + q2 * q3)
        cosr_cosp = 1.0 - 2.0 * (q1 * q1 + q2 * q2)
        roll = math.atan2(sinr_cosp, cosr_cosp)
        
        # Pitch
        sinp = 2.0 * (q0 * q2 - q3 * q1)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)
        
        # Yaw
        siny_cosp = 2.0 * (q0 * q3 + q1 * q2)
        cosy_cosp = 1.0 - 2.0 * (q2 * q2 + q3 * q3)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        return roll, pitch, yaw
    
    def stop(self):
        """Stop the worker thread."""
        self._stop_requested = True
        self._running = False
    
    def send_message(self, msg):
        """Send a MAVLink message."""
        if self._connection:
            try:
                self._connection.mav.send(msg)
                return True
            except:
                return False
        return False
    
    def send_command_long(self, command, p1=0, p2=0, p3=0, p4=0, p5=0, p6=0, p7=0):
        """Send a COMMAND_LONG message."""
        if self._connection:
            try:
                self._connection.mav.command_long_send(1, 1, command, 0, p1, p2, p3, p4, p5, p6, p7)
                return True
            except:
                return False
        return False
    
    def request_data_stream(self, stream_id: int, rate_hz: int = 50):
        """Request a specific data stream."""
        # Request at 50Hz to get more data
        if self._connection:
            try:
                self._connection.mav.request_data_stream_send(1, 1, stream_id, rate_hz, 1)
            except:
                pass


class MavlinkManager(QObject):
    """
    Manages MAVLink connections via USB or WiFi.
    Uses QThread worker for non-blocking operation.
    """
    
    # Signals
    message_received = pyqtSignal(object)
    connection_status_changed = pyqtSignal(bool)
    heartbeat_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    connection_attempt_started = pyqtSignal()
    connection_attempt_finished = pyqtSignal(bool, str)
    euler_angles = pyqtSignal(dict)  # For plotting euler angles
    
    def __init__(self):
        super().__init__()
        self._worker: Optional[ConnectionWorker] = None
        self._connected = False
        self._connecting = False
        
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    @property
    def is_connecting(self) -> bool:
        return self._connecting
    
    def _cleanup_worker(self):
        """Properly cleanup the worker thread."""
        if self._worker:
            self._worker.stop()
            
            # Wait for thread to finish with timeout
            if not self._worker.wait(2000):
                # Force terminate if it doesn't stop
                self._worker.terminate()
                self._worker.wait(500)
            
            # Disconnect all signals
            try:
                self._worker.message_received.disconnect()
                self._worker.connection_status_changed.disconnect()
                self._worker.heartbeat_received.disconnect()
                self._worker.error_occurred.disconnect()
                self._worker.connection_ready.disconnect()
                self._worker.euler_angles.disconnect()
            except:
                pass
            
            self._worker.deleteLater()
            self._worker = None
    
    def connect_usb(self, port: str, baudrate: int = 115200):
        """Connect via USB serial port."""
        if self._connecting:
            self.error_occurred.emit("Connection in progress")
            return

        self._cleanup_worker()
        
        self._connecting = True
        self.connection_attempt_started.emit()
        
        # Create and start worker thread
        self._worker = ConnectionWorker(port, is_serial=True, baudrate=baudrate)
        self._worker.message_received.connect(self.message_received.emit)
        self._worker.connection_status_changed.connect(self._on_connection_status)
        self._worker.heartbeat_received.connect(self.heartbeat_received.emit)
        self._worker.error_occurred.connect(self.error_occurred.emit)
        self._worker.connection_ready.connect(self._on_connection_ready)
        self._worker.euler_angles.connect(self.euler_angles.emit)
        self._worker.start()
    
    def connect_wifi(self, ip: str, port: int = 14550, protocol: str = "udp"):
        """Connect via WiFi (UDP or TCP)."""
        if self._connecting:
            self.error_occurred.emit("Connection in progress")
            return

        self._cleanup_worker()
        
        self._connecting = True
        self.connection_attempt_started.emit()
        
        if protocol.lower() == "udp":
            connection_string = f"udpin:{ip}:{port}"
        else:
            connection_string = f"tcp:{ip}:{port}"
        
        self._worker = ConnectionWorker(connection_string, is_serial=False)
        self._worker.message_received.connect(self.message_received.emit)
        self._worker.connection_status_changed.connect(self._on_connection_status)
        self._worker.heartbeat_received.connect(self.heartbeat_received.emit)
        self._worker.error_occurred.connect(self.error_occurred.emit)
        self._worker.connection_ready.connect(self._on_connection_ready)
        self._worker.euler_angles.connect(self.euler_angles.emit)
        self._worker.start()
    
    def _on_connection_ready(self, success: bool, message: str):
        """Handle connection attempt result."""
        self._connecting = False
        if success:
            QTimer.singleShot(500, self._request_streams)
        else:
            # Cleanup on failed connection
            self._cleanup_worker()
        self.connection_attempt_finished.emit(success, message)
    
    def _on_connection_status(self, connected: bool):
        """Handle connection status change from worker."""
        self._connected = connected
        self.connection_status_changed.emit(connected)
    
    def _request_streams(self):
        """Request all data streams."""
        if self._worker:
            self._worker.request_data_stream(0, 50)  # Request all a bit faster
    
    def disconnect(self):
        """Disconnect from the drone."""
        self._connecting = False
        self._cleanup_worker()
        self._connected = False
        self.connection_status_changed.emit(False)
    
    def send_message(self, msg):
        """Send a MAVLink message."""
        if self._worker:
            return self._worker.send_message(msg)
        return False
    
    def send_command_long(self, command: int, param1: float = 0, param2: float = 0,
                          param3: float = 0, param4: float = 0, param5: float = 0,
                          param6: float = 0, param7: float = 0,
                          target_system: int = 1, target_component: int = 1):
        """Send a COMMAND_LONG message."""
        if self._worker:
            return self._worker.send_command_long(command, param1, param2, param3, param4, param5, param6, param7)
        return False
    
    def request_data_stream(self, stream_id: int, rate_hz: int = 50):
        """Request a specific data stream."""
        if self._worker:
            self._worker.request_data_stream(stream_id, rate_hz)
    
    def request_all_streams(self, rate_hz: int = 50):
        """Request all common data streams."""
        self.request_data_stream(0, rate_hz)
