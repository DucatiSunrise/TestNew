# Main window + QTabWidget structure

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Packet Injector GUI")
        self.setGeometry(100, 100, 1000, 700)
        self.init_ui()

    def init_ui(self):
        self.tabs = QTabWidget()

        # Placeholder widgets for each tab
        self.dashboard_tab = QWidget()
        self.editor_tab = QWidget()
        self.sniffer_tab = QWidget()
        self.settings_tab = QWidget()

        # Add tabs with emojis + names
        self.tabs.addTab(self.dashboard_tab, "🏠 Main Dashboard")
        self.tabs.addTab(self.editor_tab, "🧬 Packet Editor")
        self.tabs.addTab(self.sniffer_tab, "🔍 Sniffer View")
        self.tabs.addTab(self.settings_tab, "⚙️ Settings")

        # Assign basic vertical layouts for now
        self.dashboard_tab.setLayout(QVBoxLayout())
        self.editor_tab.setLayout(QVBoxLayout())
        self.sniffer_tab.setLayout(QVBoxLayout())
        self.settings_tab.setLayout(QVBoxLayout())

        self.setCentralWidget(self.tabs)

def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
