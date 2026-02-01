"""
Main Application Window for SPAM-GCS.
"""

import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QComboBox, QLineEdit, QPushButton, QFrame, QMessageBox,
    QProgressDialog, QMenu
)
from PyQt5.QtCore import Qt, QTimer, QPoint

from src.theme.styles import apply_theme
from src.connection.mavlink_manager import MavlinkManager, ConnectionType
from src.connection.message_broker import MessageBroker
from src.logging.mavlink_logger import MavlinkLogger
from src.pages.general_page import GeneralPage
from src.pages.debug_page import DebugPage
from src.pages.settings_page import SettingsPage


class UndockedWindow(QMainWindow):
    """Container window for undocked tabs."""
    
    def __init__(self, widget, title, original_index, main_window, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"SPAM-GCS - {title}")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        self._widget = widget
        self._original_title = title
        self._original_index = original_index
        self._main_window = main_window
        
        # Create a container widget to hold the content
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        
        self.setCentralWidget(container)
        
        # Ensure the widget is visible
        widget.show()
    
    def get_title(self):
        return self._original_title
    
    def get_widget(self):
        return self._widget
    
    def get_original_index(self):
        return self._original_index
    
    def closeEvent(self, event):
        """Redock the tab when window is closed."""
        # Remove widget from our layout before redocking
        if self._widget and self._main_window:
            # Reparent widget to main window's tab widget
            self._widget.setParent(None)
            self._main_window.redock_tab(self._widget, self._original_title, self._original_index)
        event.accept()


class MainWindow(QMainWindow):
    """Main application window with connection bar and tabbed pages."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.mavlink_manager = MavlinkManager()
        self.message_broker = MessageBroker()
        self.logger = MavlinkLogger(self.message_broker)
        self._undocked_windows = []  # Track undocked windows
        
        # Connect signals
        self.mavlink_manager.message_received.connect(self._on_message_received)
        self.mavlink_manager.connection_status_changed.connect(self._on_connection_changed)
        self.mavlink_manager.heartbeat_received.connect(self._on_heartbeat)
        self.mavlink_manager.error_occurred.connect(self._on_error)
        self.mavlink_manager.connection_attempt_started.connect(self._on_connection_attempt_started)
        self.mavlink_manager.connection_attempt_finished.connect(self._on_connection_attempt_finished)
        
        # Setup UI
        self._setup_window()
        self._setup_ui()
        
        # Apply theme
        apply_theme(self.window())
        
        # Start port refresh timer
        self._port_refresh_timer = QTimer()
        self._port_refresh_timer.timeout.connect(self._refresh_ports)
        self._port_refresh_timer.start(2000)  # Refresh every 2 seconds
        self._refresh_ports()
    
    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle("SPAM-GCS - Ground Control Station")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
    
    def _setup_ui(self):
        """Build the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Connection bar
        connection_frame = QFrame()
        connection_frame.setObjectName("connectionFrame")
        connection_layout = QHBoxLayout(connection_frame)
        connection_layout.setContentsMargins(12, 8, 12, 8)
        
        # Connection type selector
        type_label = QLabel("Connection:")
        connection_layout.addWidget(type_label)
        
        self.connection_type = QComboBox()
        self.connection_type.addItems(["USB", "WiFi"])
        self.connection_type.currentIndexChanged.connect(self._on_connection_type_changed)
        connection_layout.addWidget(self.connection_type)
        
        # USB options
        self.usb_widget = QWidget()
        usb_layout = QHBoxLayout(self.usb_widget)
        usb_layout.setContentsMargins(0, 0, 0, 0)
        
        port_label = QLabel("Port:")
        usb_layout.addWidget(port_label)
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        usb_layout.addWidget(self.port_combo)
        
        baud_label = QLabel("Baud:")
        usb_layout.addWidget(baud_label)
        
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["921600", "57600", "115200", "460800"])
        self.baud_combo.setCurrentIndex(0)  # Default to 921600
        usb_layout.addWidget(self.baud_combo)
        
        connection_layout.addWidget(self.usb_widget)
        
        # WiFi options
        self.wifi_widget = QWidget()
        wifi_layout = QHBoxLayout(self.wifi_widget)
        wifi_layout.setContentsMargins(0, 0, 0, 0)
        
        ip_label = QLabel("IP:Port:")
        wifi_layout.addWidget(ip_label)
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.1:14550")
        self.ip_input.setText("0.0.0.0:14550")
        self.ip_input.setMinimumWidth(150)
        wifi_layout.addWidget(self.ip_input)
        
        protocol_label = QLabel("Protocol:")
        wifi_layout.addWidget(protocol_label)
        
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["UDP", "TCP"])
        wifi_layout.addWidget(self.protocol_combo)
        
        connection_layout.addWidget(self.wifi_widget)
        self.wifi_widget.hide()
        
        connection_layout.addStretch()
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #f87171; font-size: 16px;")
        connection_layout.addWidget(self.status_indicator)
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setObjectName("statusDisconnected")
        connection_layout.addWidget(self.status_label)
        
        connection_layout.addSpacing(16)
        
        # Connect/Disconnect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        connection_layout.addWidget(self.connect_btn)
        
        # Log toggle button
        self.log_btn = QPushButton("Log")
        self.log_btn.setCheckable(True)
        self.log_btn.clicked.connect(self._on_log_clicked)
        self.log_btn.setStyleSheet("""
            QPushButton { background-color: #374151; }
            QPushButton:checked { background-color: #dc2626; }
        """)
        connection_layout.addWidget(self.log_btn)
        
        main_layout.addWidget(connection_frame)
        
        # Tab widget for pages
        self.tab_widget = QTabWidget()
        
        # Enable right-click context menu on tab bar
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(self._on_tab_context_menu)
        
        # Create pages
        self.general_page = GeneralPage(self.message_broker)
        self.debug_page = DebugPage(self.message_broker)
        self.settings_page = SettingsPage(self.message_broker, self.mavlink_manager)
        
        self.tab_widget.addTab(self.general_page, "General")
        self.tab_widget.addTab(self.debug_page, "Debug")
        self.tab_widget.addTab(self.settings_page, "Settings")
        
        main_layout.addWidget(self.tab_widget, 1)
    
    def _on_connection_type_changed(self, index):
        """Handle connection type selection change."""
        if index == 0:  # USB
            self.usb_widget.show()
            self.wifi_widget.hide()
        else:  # WiFi
            self.usb_widget.hide()
            self.wifi_widget.show()
    
    def _refresh_ports(self):
        """Refresh available serial ports."""
        current_port = self.port_combo.currentText()
        self.port_combo.clear()
        
        ports = serial.tools.list_ports.comports()
        port_names = [p.device for p in ports]
        self.port_combo.addItems(port_names)
        
        # Restore selection if still available
        if current_port in port_names:
            self.port_combo.setCurrentText(current_port)
    
    def _on_connect_clicked(self):
        """Handle connect/disconnect button click."""
        if self.mavlink_manager.is_connected or self.mavlink_manager.is_connecting:
            self.mavlink_manager.disconnect()
        else:
            self._connect()
    
    def _connect(self):
        """Establish connection based on selected type."""
        if self.connection_type.currentIndex() == 0:  # USB
            port = self.port_combo.currentText()
            if not port:
                QMessageBox.warning(self, "Connection Error", "Please select a serial port.")
                return
            
            baudrate = int(self.baud_combo.currentText())
            self.mavlink_manager.connect_usb(port, baudrate)
        else:  # WiFi
            ip_port = self.ip_input.text()
            if ":" not in ip_port:
                QMessageBox.warning(self, "Connection Error", "Please enter IP:Port format.")
                return
            
            ip, port = ip_port.rsplit(":", 1)
            protocol = self.protocol_combo.currentText().lower()
            self.mavlink_manager.connect_wifi(ip, int(port), protocol)
    
    def _on_connection_attempt_started(self):
        """Handle connection attempt started."""
        self.connect_btn.setText("Connecting...")
        self.connect_btn.setEnabled(True)  # Keep enabled so user can cancel
        self.status_label.setText("Connecting...")
        self.status_indicator.setStyleSheet("color: #fbbf24; font-size: 16px;")  # Yellow
    
    def _on_connection_attempt_finished(self, success: bool, message: str):
        """Handle connection attempt finished."""
        self.connect_btn.setEnabled(True)
        
        if success:
            # Request data streams
            QTimer.singleShot(500, self._request_streams)
        else:
            # Show error message
            self.status_indicator.setStyleSheet("color: #f87171; font-size: 16px;")
            self.status_label.setText("Disconnected")
            self.connect_btn.setText("Connect")
            QMessageBox.warning(self, "Connection Failed", message)
    
    def _request_streams(self):
        """Request MAVLink data streams after connection."""
        self.mavlink_manager.request_all_streams(10)
    
    def _on_connection_changed(self, connected: bool):
        """Handle connection status change."""
        if connected:
            self.status_indicator.setStyleSheet("color: #4ade80; font-size: 16px;")
            self.status_label.setText("Connected")
            self.status_label.setObjectName("statusConnected")
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setObjectName("disconnectBtn")
        else:
            self.status_indicator.setStyleSheet("color: #f87171; font-size: 16px;")
            self.status_label.setText("Disconnected")
            self.status_label.setObjectName("statusDisconnected")
            self.connect_btn.setText("Connect")
            self.connect_btn.setObjectName("")
        
        self.connect_btn.setEnabled(True)
        self.settings_page.set_connected(connected)
        
        # Force style refresh
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.connect_btn.style().unpolish(self.connect_btn)
        self.connect_btn.style().polish(self.connect_btn)
    
    def _on_heartbeat(self, heartbeat_data: dict):
        """Handle heartbeat message."""
        # Update status with flight mode if available
        mode = heartbeat_data.get('custom_mode', 0)
        self.status_label.setText(f"Connected (Mode: {mode})")
    
    def _on_message_received(self, msg):
        """Handle received MAVLink message."""
        self.message_broker.publish(msg)
    
    def _on_error(self, error_msg: str):
        """Handle connection error."""
        QMessageBox.warning(self, "Error", error_msg)
    
    def _on_tab_context_menu(self, pos: QPoint):
        """Handle right-click context menu on tab bar."""
        tab_bar = self.tab_widget.tabBar()
        tab_index = tab_bar.tabAt(pos)
        
        if tab_index >= 0:
            menu = QMenu(self)
            undock_action = menu.addAction("Undock Tab")
            
            action = menu.exec_(tab_bar.mapToGlobal(pos))
            if action == undock_action:
                self._undock_tab(tab_index)
    
    def _undock_tab(self, index: int):
        """Undock a tab into a separate window."""
        if index < 0 or index >= self.tab_widget.count():
            return
        
        # Get tab info before removing
        widget = self.tab_widget.widget(index)
        title = self.tab_widget.tabText(index)
        
        # Remove from tab widget
        self.tab_widget.removeTab(index)
        
        # Create undocked window (pass index for restore position)
        undocked = UndockedWindow(widget, title, original_index=index, main_window=self)
        
        # Apply theme to match main window
        apply_theme(undocked)
        
        undocked.show()
        
        # Track the window
        self._undocked_windows.append(undocked)
    
    def redock_tab(self, widget, title, original_index):
        """Redock a widget back into the tab widget at its original position."""
        # Insert at original position, clamping to valid range
        insert_index = min(original_index, self.tab_widget.count())
        self.tab_widget.insertTab(insert_index, widget, title)
        self.tab_widget.setCurrentIndex(insert_index)
        widget.show()
        
        # Remove from undocked windows list
        for window in self._undocked_windows[:]:
            if window.get_widget() == widget:
                self._undocked_windows.remove(window)
                break
    
    def closeEvent(self, event):
        """Clean up on window close."""
        # Stop logger first to ensure data is saved
        if self.logger.is_logging:
            self.logger.stop()
        
        self.mavlink_manager.disconnect()
        self._port_refresh_timer.stop()
        
        # Close all undocked windows without redocking
        # Set main_window to None to prevent redock attempts
        for window in self._undocked_windows[:]:
            window._main_window = None
            window.close()
        self._undocked_windows.clear()
        
        event.accept()

    def _on_log_clicked(self, checked: bool):
        """Handle log button toggle."""
        if checked:
            log_path = self.logger.start()
            self.log_btn.setText("Stop Log")
        else:
            self.logger.stop()
            self.log_btn.setText("Log")
