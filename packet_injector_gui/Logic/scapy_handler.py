import os
import builtins

# 🧠 Patch only if provided by main.py
if hasattr(builtins, "__SCAPY_CACHE_PATCH__"):
    os.environ["SCAPY_CACHE"] = builtins.__SCAPY_CACHE_PATCH__

# ✅ Don't import Scapy here — move inside functions instead


def list_interfaces():
    from scapy.all import get_if_list
    return get_if_list()


def start_sniffer(iface, callback, bpf_filter=None):
    from scapy.all import AsyncSniffer
    return AsyncSniffer(
        iface=iface,
        prn=callback,
        filter=bpf_filter,
        store=False
    )


def build_sample_packet():
    from scapy.all import Ether, IP, TCP, Raw
    return (
        Ether() /
        IP(src="192.168.1.100", dst="192.168.1.1") /
        TCP(sport=1234, dport=80, flags="S") /
        Raw(load="GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
    )


def send_packet(packet):
    from scapy.all import send
    send(packet)
