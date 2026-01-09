"""
Attitude Indicator Widget - Graphical artificial horizon display.
Converts quaternion to euler angles for display.
"""

import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QLinearGradient, QPainterPath, QPolygonF


def quaternion_to_euler(q0, q1, q2, q3):
    """
    Convert quaternion (w, x, y, z) to euler angles (roll, pitch, yaw) in radians.
    Uses aerospace convention (NED frame, ZYX rotation order).
    """
    # Roll (x-axis rotation)
    sinr_cosp = 2.0 * (q0 * q1 + q2 * q3)
    cosr_cosp = 1.0 - 2.0 * (q1 * q1 + q2 * q2)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    
    # Pitch (y-axis rotation)
    sinp = 2.0 * (q0 * q2 - q3 * q1)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)
    else:
        pitch = math.asin(sinp)
    
    # Yaw (z-axis rotation)
    siny_cosp = 2.0 * (q0 * q3 + q1 * q2)
    cosy_cosp = 1.0 - 2.0 * (q2 * q2 + q3 * q3)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    
    return roll, pitch, yaw


class AttitudeIndicator(QWidget):
    """
    Graphical attitude indicator (artificial horizon) widget.
    Full-featured with sky/ground, pitch ladder, bank angle indicator.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        
        self.setMinimumSize(180, 180)
        
        # Colors - richer sky/ground but more muted for modern look
        self.sky_top = QColor(40, 100, 160)
        self.sky_bottom = QColor(80, 140, 200)
        self.ground_top = QColor(100, 70, 40)
        self.ground_bottom = QColor(60, 40, 20)
        self.horizon_color = QColor(255, 255, 255)
        self.aircraft_color = QColor(255, 180, 0)
        
    def set_attitude_quaternion(self, q0, q1, q2, q3):
        """Update attitude from quaternion (w, x, y, z)."""
        self.roll, self.pitch, self.yaw = quaternion_to_euler(q0, q1, q2, q3)
        self.update()
    
    def set_attitude_euler(self, roll, pitch, yaw):
        """Update attitude from euler angles (radians)."""
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.update()
    
    def paintEvent(self, event):
        """Draw the attitude indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        size = min(width, height) - 4  # Minimal padding
        radius = size // 2
        center_x = width // 2
        center_y = height // 2
        
        # Create circular clipping region
        clip_path = QPainterPath()
        clip_path.addEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        painter.setClipPath(clip_path)
        
        # Save state and move to center
        painter.save()
        painter.translate(center_x, center_y)
        
        # Apply roll rotation
        painter.rotate(math.degrees(-self.roll))
        
        # Calculate pitch offset
        pitch_scale = radius / 30.0  # 30 degrees = full radius
        pitch_offset = int(math.degrees(self.pitch) * pitch_scale)
        
        # Draw sky gradient
        sky_rect = QRectF(-radius * 2, -radius * 2 + pitch_offset, radius * 4, radius * 2)
        sky_gradient = QLinearGradient(0, -radius * 2 + pitch_offset, 0, pitch_offset)
        sky_gradient.setColorAt(0, self.sky_top)
        sky_gradient.setColorAt(1, self.sky_bottom)
        painter.fillRect(sky_rect, sky_gradient)
        
        # Draw ground gradient
        ground_rect = QRectF(-radius * 2, pitch_offset, radius * 4, radius * 2)
        ground_gradient = QLinearGradient(0, pitch_offset, 0, radius * 2 + pitch_offset)
        ground_gradient.setColorAt(0, self.ground_top)
        ground_gradient.setColorAt(1, self.ground_bottom)
        painter.fillRect(ground_rect, ground_gradient)
        
        # Draw horizon line
        painter.setPen(QPen(self.horizon_color, 2))
        painter.drawLine(-radius * 2, pitch_offset, radius * 2, pitch_offset)
        
        # Draw pitch ladder
        painter.setPen(QPen(Qt.white, 1))
        font = QFont("Arial", 8)  # Slightly larger font
        font.setBold(True)
        painter.setFont(font)
        
        for deg in [-20, -15, -10, -5, 5, 10, 15, 20]:
            y = int(pitch_offset - deg * pitch_scale)
            line_width = 25 if abs(deg) == 10 or abs(deg) == 20 else 15
            
            # Draw pitch lines with gap in center
            if deg > 0:  # Above horizon (nose up)
                painter.drawLine(-line_width, y, -5, y)
                painter.drawLine(5, y, line_width, y)
                # Small end ticks pointing down
                painter.drawLine(-line_width, y, -line_width, y + 5)
                painter.drawLine(line_width, y, line_width, y + 5)
            else:  # Below horizon (nose down)
                # Dashed line for below horizon
                painter.drawLine(-line_width, y, -5, y)
                painter.drawLine(5, y, line_width, y)
                # Small end ticks pointing up
                painter.drawLine(-line_width, y, -line_width, y - 5)
                painter.drawLine(line_width, y, line_width, y - 5)
            
            # Draw degree labels
            if abs(deg) % 10 == 0:
                painter.drawText(line_width + 4, y + 3, str(abs(deg)))
                painter.drawText(-line_width - 18, y + 3, str(abs(deg)))
        
        painter.restore()
        
        # Clear clipping for fixed elements
        painter.setClipRect(0, 0, width, height)
        painter.translate(center_x, center_y)
        
        # Draw aircraft reference symbol (fixed)
        painter.setPen(QPen(self.aircraft_color, 3))
        # Left wing
        painter.drawLine(-60, 0, -20, 0)
        painter.drawLine(-20, 0, -20, 6)
        # Right wing  
        painter.drawLine(60, 0, 20, 0)
        painter.drawLine(20, 0, 20, 6)
        # Center
        painter.setBrush(self.aircraft_color)
        painter.drawEllipse(-6, -6, 12, 12)
        
        # Draw bank angle arc at top
        painter.setPen(QPen(Qt.white, 2))
        arc_radius = radius - 8
        
        # Bank angle tick marks
        for angle in [0, 10, 20, 30, 45, 60]:
            for sign in [1, -1]:
                a = math.radians(90 + sign * angle)
                r1 = arc_radius - (8 if angle % 30 == 0 else 5)
                r2 = arc_radius
                x1 = int(r1 * math.cos(a))
                y1 = int(-r1 * math.sin(a))
                x2 = int(r2 * math.cos(a))
                y2 = int(-r2 * math.sin(a))
                painter.drawLine(x1, y1, x2, y2)
        
        # Draw bank pointer (rotates with roll)
        painter.save()
        painter.rotate(math.degrees(-self.roll))
        painter.setPen(QPen(self.aircraft_color, 2))
        painter.setBrush(self.aircraft_color)
        triangle = QPolygonF([
            QPointF(0, -arc_radius + 12),
            QPointF(-6, -arc_radius + 2),
            QPointF(6, -arc_radius + 2)
        ])
        painter.drawPolygon(triangle)
        painter.restore()
        
        # Draw fixed triangle at top (sky pointer)
        painter.setPen(QPen(Qt.white, 1))
        painter.setBrush(Qt.white)
        sky_triangle = QPolygonF([
            QPointF(0, -arc_radius - 2),
            QPointF(-6, -arc_radius - 10),
            QPointF(6, -arc_radius - 10)
        ])
        painter.drawPolygon(sky_triangle)
        
        painter.end()


class AttitudeWidget(QWidget):
    """Container widget with attitude indicator and numeric display."""
    
    def __init__(self, message_broker, parent=None):
        super().__init__(parent)
        self.message_broker = message_broker
        self._setup_ui()
        self._subscribe_to_messages()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        self.attitude_indicator = AttitudeIndicator()
        layout.addWidget(self.attitude_indicator)
        
        # Modern, clean numeric display
        self.numeric_label = QLabel("R: ---  P: ---  Y: ---")
        self.numeric_label.setAlignment(Qt.AlignCenter)
        self.numeric_label.setStyleSheet(
            "font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: bold; color: #ddd; letter-spacing: 0.5px;"
        )
        layout.addWidget(self.numeric_label)
    
    def _subscribe_to_messages(self):
        """Subscribe to attitude messages."""
        self.message_broker.subscribe('ATTITUDE_QUATERNION', self._on_attitude_quaternion)
        self.message_broker.subscribe('ATTITUDE', self._on_attitude)
    
    def _on_attitude_quaternion(self, msg):
        """Handle ATTITUDE_QUATERNION message."""
        self.attitude_indicator.set_attitude_quaternion(msg.q1, msg.q2, msg.q3, msg.q4)
        self._update_label()
    
    def _on_attitude(self, msg):
        """Handle ATTITUDE message."""
        self.attitude_indicator.set_attitude_euler(msg.roll, msg.pitch, msg.yaw)
        self._update_label()
    
    def _update_label(self):
        """Update numeric label."""
        roll_deg = math.degrees(self.attitude_indicator.roll)
        pitch_deg = math.degrees(self.attitude_indicator.pitch)
        yaw_deg = math.degrees(self.attitude_indicator.yaw)
        self.numeric_label.setText(
            f"R {roll_deg:+.1f}°   P {pitch_deg:+.1f}°   Y {yaw_deg:+.1f}°"
        )
