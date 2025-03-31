# Main window + QTabWidget structure

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
from ui.main_dashboard import PacketOverviewPanel
from ui.sniffer_view import SnifferView
import sys
from logic.scapy_handler import build_sample_packet

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Packet Injector GUI")
        self.setGeometry(100, 100, 1000, 700)
        self.init_ui()
        self.setFixedSize(self.size())

    def handle_sniffed_packet(self, packet):
        # Update the packet viewer (and optionally add to queue)
        self.overview_panel.update_packet(packet)

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

        # Main Dashboard layout
        self.overview_panel = PacketOverviewPanel()
        dashboard_layout = QVBoxLayout()
        dashboard_layout.addWidget(self.overview_panel)
        self.dashboard_tab.setLayout(dashboard_layout)

        # Inject a sample Scapy packet into the overview
        sample_packet = build_sample_packet()
        self.overview_panel.update_packet(sample_packet)

        # Create the Sniffer View and set it as the sniffer tab
        self.sniffer_view = SnifferView(packet_callback=self.handle_sniffed_packet)
        sniffer_layout = QVBoxLayout()
        sniffer_layout.addWidget(self.sniffer_view)
        self.sniffer_tab.setLayout(sniffer_layout)

        # Other tabs stay empty for now
        self.editor_tab.setLayout(QVBoxLayout())
        self.settings_tab.setLayout(QVBoxLayout())

        self.setCentralWidget(self.tabs)

def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
