# Layout & widgets for Sniffer View tab
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QTextEdit, QGroupBox, QLineEdit
)
from PyQt6.QtCore import QThread, pyqtSignal
from logic.scapy_handler import list_interfaces, start_sniffer

class SnifferThread(QThread):
    packet_captured = pyqtSignal(object)

    def __init__(self, iface, bpf_filter=None):
        super().__init__()
        self.iface = iface
        self.bpf_filter = bpf_filter
        self.running = True
        self.sniffer = None

    def run(self):
        self.sniffer = start_sniffer(
            iface=self.iface,
            callback=self.handle_packet,
            bpf_filter=self.bpf_filter
        )
        self.sniffer.start()
        self.sniffer.join()  # Keep thread alive while sniffing

    def handle_packet(self, packet):
        if self.running:
            self.packet_captured.emit(packet)

    def stop(self):
        self.running = False
        if self.sniffer:
            self.sniffer.stop()

class SnifferView(QWidget):
    def __init__(self, packet_callback, parent=None):
        super().__init__(parent)
        self.packet_callback = packet_callback
        self.sniffer_thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Interface and filter selection
        control_box = QGroupBox("Sniffer Controls")
        control_layout = QHBoxLayout()

        self.interface_dropdown = QComboBox()
        self.interface_dropdown.addItems(list_interfaces())

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Optional BPF filter (e.g., tcp port 80)")

        self.start_button = QPushButton("Start Sniffing")
        self.stop_button = QPushButton("Stop Sniffing")
        self.stop_button.setEnabled(False)

        self.start_button.clicked.connect(self.start_sniffer)
        self.stop_button.clicked.connect(self.stop_sniffer)

        control_layout.addWidget(QLabel("Interface:"))
        control_layout.addWidget(self.interface_dropdown)
        control_layout.addWidget(QLabel("Filter:"))
        control_layout.addWidget(self.filter_input)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)

        control_box.setLayout(control_layout)
        layout.addWidget(control_box)

        # Log output
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        layout.addWidget(self.output_log)

        self.setLayout(layout)

    def start_sniffer(self):
        iface = self.interface_dropdown.currentText()
        bpf_filter = self.filter_input.text() or None

        self.sniffer_thread = SnifferThread(iface=iface, bpf_filter=bpf_filter)
        self.sniffer_thread.packet_captured.connect(self.on_packet_captured)
        self.sniffer_thread.start()

        self.output_log.append(f"[+] Started sniffing on {iface} with filter: {bpf_filter or 'None'}")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_sniffer(self):
        if self.sniffer_thread:
            self.sniffer_thread.stop()
            self.sniffer_thread.wait()
            self.output_log.append("[-] Sniffing stopped.")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def on_packet_captured(self, packet):
        self.output_log.append(f"[*] Packet captured: {packet.summary()}")
        self.packet_callback(packet)  # Pass packet to main viewer or queue
