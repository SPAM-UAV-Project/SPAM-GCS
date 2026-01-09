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

/* Tab Widget - Minimalist */
QTabWidget::pane {
    border: none;
    background-color: #1a1a2e;
    margin-top: 8px;
}

QTabBar::tab {
    background-color: transparent;
    color: #888;
    padding: 10px 24px;  /* Increased padding to prevent clipping */
    margin-right: 16px;
    font-weight: 600;
    font-size: 14px;
    border: none;
    min-width: 80px;    /* Minimum width to ensure space */
}

QTabBar::tab:selected {
    color: #ffffff;
    border-bottom: 2px solid #6c63ff;
}

QTabBar::tab:hover:!selected {
    color: #ccccff;
}

/* Buttons */
QPushButton {
    background-color: #6c63ff;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 13px;
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
    background-color: #ef4444;
}

QPushButton#disconnectBtn:hover {
    background-color: #f87171;
}

/* ComboBox - Modern Flat */
QComboBox {
    background-color: #252540;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 12px;
    min-width: 100px;
    color: #eaeaea;
}

QComboBox:hover {
    background-color: #2d2d48;
}

QComboBox:on {
    padding-top: 3px;
    padding-left: 4px;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #888;
    margin-right: 8px;
    margin-top: 2px;
}

QComboBox QAbstractItemView {
    background-color: #252540;
    border: 1px solid #3a3a5c;
    selection-background-color: #6c63ff;
    color: #eaeaea;
    outline: none;
}

/* LineEdit */
QLineEdit {
    background-color: #252540;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 12px;
    color: #eaeaea;
}

QLineEdit:focus {
    background-color: #2d2d48;
    border: 1px solid #6c63ff;
}

/* Labels */
QLabel {
    color: #eaeaea;
}

QLabel#sectionTitle {
    font-size: 11px;
    font-weight: 700;
    color: #888;
    letter-spacing: 1px;
    padding: 4px 0;
    text-transform: uppercase;
}

/* Frame */
QFrame#connectionFrame {
    background-color: transparent;
    border: none;
    padding: 4px;
}

QFrame#statusCard {
    background-color: transparent;
    border: none;
}

/* Splitter */
QSplitter::handle {
    background-color: transparent;
}
"""


def apply_theme(app):
    """Apply the dark theme to the application."""
    app.setStyleSheet(DARK_THEME)
