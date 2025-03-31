# logic/scapy_handler.py
import os
import builtins

# Patch SCAPY_CACHE
if hasattr(builtins, "__SCAPY_CACHE_PATCH__"):
    os.environ["SCAPY_CACHE"] = builtins.__SCAPY_CACHE_PATCH__

from scapy.all import (
    sniff, get_if_list, AsyncSniffer,
    Ether, IP, TCP, Raw, send
)

def list_interfaces():
    return get_if_list()

def start_sniffer(iface, callback, bpf_filter=None):
    return AsyncSniffer(
        iface=iface,
        prn=callback,
        filter=bpf_filter,
        store=False
    )

def build_sample_packet():
    return (
        Ether() /
        IP(src="192.168.1.100", dst="192.168.1.1") /
        TCP(sport=1234, dport=80, flags="S") /
        Raw(load="GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
    )

def send_packet(packet):
    send(packet)
