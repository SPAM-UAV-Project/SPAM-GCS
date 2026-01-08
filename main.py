"""
SPAM-GCS: Drone Ground Control Station
Entry point for the application.
"""

import sys
from PyQt5.QtWidgets import QApplication
from src.app import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
