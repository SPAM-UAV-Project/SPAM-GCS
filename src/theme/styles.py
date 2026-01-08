"""
Modern dark theme styles for SPAM-GCS.
"""

DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #eaeaea;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #2d2d44;
    background-color: #1a1a2e;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #252540;
    color: #a0a0a0;
    padding: 10px 24px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #3a3a5c;
    color: #ffffff;
    border-bottom: 2px solid #6c63ff;
}

QTabBar::tab:hover:!selected {
    background-color: #2d2d48;
}

/* Buttons */
QPushButton {
    background-color: #6c63ff;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #7d75ff;
}

QPushButton:pressed {
    background-color: #5a52e0;
}

QPushButton:disabled {
    background-color: #3a3a5c;
    color: #666666;
}

QPushButton#disconnectBtn {
    background-color: #ff6b6b;
}

QPushButton#disconnectBtn:hover {
    background-color: #ff8585;
}

/* ComboBox */
QComboBox {
    background-color: #252540;
    border: 1px solid #3a3a5c;
    border-radius: 4px;
    padding: 6px 12px;
    min-width: 100px;
    color: #eaeaea;
}

QComboBox:hover {
    border-color: #6c63ff;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #252540;
    border: 1px solid #3a3a5c;
    selection-background-color: #6c63ff;
    color: #eaeaea;
}

/* LineEdit */
QLineEdit {
    background-color: #252540;
    border: 1px solid #3a3a5c;
    border-radius: 4px;
    padding: 6px 12px;
    color: #eaeaea;
}

QLineEdit:focus {
    border-color: #6c63ff;
}

/* Labels */
QLabel {
    color: #eaeaea;
}

QLabel#sectionTitle {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
    padding: 8px 0;
}

QLabel#statusConnected {
    color: #4ade80;
    font-weight: bold;
}

QLabel#statusDisconnected {
    color: #f87171;
    font-weight: bold;
}

/* Group Box */
QGroupBox {
    border: 1px solid #3a3a5c;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #a0a0ff;
}

/* Progress Bar (for RC channels) */
QProgressBar {
    background-color: #252540;
    border: none;
    border-radius: 3px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #6c63ff;
    border-radius: 3px;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #3a3a5c;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a4a6c;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* Frame */
QFrame#connectionFrame {
    background-color: #252540;
    border-radius: 6px;
    padding: 8px;
}

QFrame#statusCard {
    background-color: #252540;
    border-radius: 8px;
    padding: 12px;
}

/* Splitter */
QSplitter::handle {
    background-color: #3a3a5c;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}
"""


def apply_theme(app):
    """Apply the dark theme to the application."""
    app.setStyleSheet(DARK_THEME)
