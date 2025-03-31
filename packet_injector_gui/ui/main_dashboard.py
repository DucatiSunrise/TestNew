from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QGroupBox, QListWidget, QPushButton, QListWidgetItem, QFrame
)
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor
from PyQt6.QtCore import Qt

class PacketOverviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Split top section: Summary and Hex view
        top_layout = QHBoxLayout()

        # Left: Layered Summary
        self.summary_layout = QVBoxLayout()
        self.summary_group = QGroupBox("🧩 Layered Packet Summary")
        self.summary_group.setLayout(self.summary_layout)

        # Create clickable TCP label
        tcp_label = QLabel('<a href="#">TCP: Src Port → <b>Dst Port</b>, Flags</a>')
        tcp_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        tcp_label.setCursor(Qt.CursorShape.PointingHandCursor)
        tcp_label.setOpenExternalLinks(False)
        tcp_label.linkActivated.connect(self.highlight_dst_port)

        # Create the rest of the field labels
        self.fields = {
            "Ethernet": QLabel("Ethernet: Src → Dst"),
            "IP": QLabel("IP: Src → Dst, TTL"),
            "TCP": tcp_label,  # ← clickable version
            "HTTP": QLabel("HTTP: GET /index.html"),
        }

        for label in self.fields.values():
            label.setFont(QFont("Courier", 10))
            self.summary_layout.addWidget(label)

        # Right: Hexadecimal View
        self.hex_view = QPlainTextEdit()
        self.hex_view.setReadOnly(True)
        self.hex_view.setFont(QFont("Courier", 10))
        self.hex_view.setPlainText("00 1a 2b 3c 4d 5e  60 7f 80 9a ab cd ...")

        hex_group = QGroupBox("🔎 Raw Hexadecimal View")
        hex_layout = QVBoxLayout()
        hex_layout.addWidget(self.hex_view)
        hex_group.setLayout(hex_layout)

        top_layout.addWidget(self.summary_group, 1)
        top_layout.addWidget(hex_group, 2)

        # Bottom: Packet Queue and Control Buttons
        bottom_layout = QVBoxLayout()
        self.packet_list = QListWidget()
        self.packet_list.setFont(QFont("Courier", 9))

        button_row = QHBoxLayout()
        self.btn_add = QPushButton("Add Packet")
        self.btn_edit = QPushButton("Edit Packet")
        self.btn_delete = QPushButton("Delete Packet")
        self.btn_send = QPushButton("Send Packet")
        self.btn_compare = QPushButton("Compare")

        for btn in [self.btn_add, self.btn_edit, self.btn_delete, self.btn_send, self.btn_compare]:
            button_row.addWidget(btn)

        bottom_layout.addWidget(QLabel("\ud83d\udce6 Packet Queue"))
        bottom_layout.addWidget(self.packet_list)
        bottom_layout.addLayout(button_row)

        # Final Layout
        main_layout.addLayout(top_layout, 3)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)
        main_layout.addLayout(bottom_layout, 2)

        self.setLayout(main_layout)

    def update_packet(self, packet):
        self.current_packet = packet
        # Ethernet layer
        if packet.haslayer("Ether"):
            eth = packet.getlayer("Ether")
            self.fields["Ethernet"].setText(f"Ethernet: {eth.src} → {eth.dst}")

        # IP layer
        if packet.haslayer("IP"):
            ip = packet.getlayer("IP")
            self.fields["IP"].setText(f"IP: {ip.src} → {ip.dst}, TTL: {ip.ttl}")

        # TCP layer
        if packet.haslayer("TCP"):
            tcp = packet.getlayer("TCP")
            flags = str(tcp.flags)
            self.fields["TCP"].setText(f"TCP: {tcp.sport} → {tcp.dport}, Flags: {flags}")

        # HTTP / Raw layer
        if packet.haslayer("Raw"):
            raw = packet.getlayer("Raw").load
            preview = raw.decode(errors="ignore")
            self.fields["HTTP"].setText(f"HTTP: {preview[:50]}...")

        # Hex view with ASCII (Wireshark style)
        raw_bytes = bytes(packet)
        lines = []

        for offset in range(0, len(raw_bytes), 16):
            chunk = raw_bytes[offset:offset+16]
            hex_bytes = " ".join(f"{b:02x}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            line = f"{offset:04x}  {hex_bytes:<47}  {ascii_part}"
            lines.append(line)

        self.hex_view.setPlainText("\n".join(lines))

    def highlight_dst_port(self):
        print("[DEBUG] TCP Dst Port label clicked")
        packet = self.current_packet
        if not packet or not packet.haslayer("TCP"):
            return

        # TCP dst port starts at byte 16 (Ethernet + 2 bytes into TCP)
        offset = 14 + 2
        raw_bytes = bytes(packet)
        if len(raw_bytes) <= offset + 1:
            return

        # Find the starting character position in the hex view
        hex_text = self.hex_view.toPlainText()
        lines = hex_text.splitlines()

        byte_index = 0
        char_index = 0
        start_pos = None
        end_pos = None

        for line in lines:
            parts = line.strip().split()
            if len(parts) < 2:
                continue

            hex_part = parts[1:17]  # skip offset
            for hex_byte in hex_part:
                if byte_index == offset:
                    start_pos = char_index
                if byte_index == offset + 2:
                    end_pos = char_index
                    break

                char_index += len(hex_byte) + 1  # 2 hex + space
                byte_index += 1

            if end_pos is not None:
                break
            char_index += 1  # for newline

        if start_pos is not None and end_pos is not None:
            cursor = self.hex_view.textCursor()
            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)

            fmt = QTextCharFormat()
            fmt.setBackground(QColor("yellow"))
            print(f"Highlighting hex from char {start_pos} to {end_pos}")
            cursor.setCharFormat(fmt)
