#!/usr/bin/python                                                                            
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel

class Dumbbell_topology(Topo):
    "Dumbbell Topology - 4 hosts with 4 routers"
    def build(self, Packet_size_bytes=60):
        #Packet Size is in Bytes

        #Assignment Constants:
        BIT_TO_BYTES = 8
        HOST_PACKET_MS = 80
        AR_BR_PACKET_MS = 21
        BR_BR_PACKET_MS = 82
        BR_BR_DELAY_SHORT = '21ms'
        BR_BR_DELAY_MEDIUM = '81ms'
        BR_BR_DELAY_LONG = '162ms'

        #Create the 4 routers
        #AR = Access Router
        #BR = Backbone Router
        AR1 = self.addSwitch('AR1')
        AR2 = self.addSwitch('AR2')
        BR2 = self.addSwitch('BR2')
        BR1 = self.addSwitch('BR1')

        #Create the 4 hosts
        #S = Source
        #R = Receiver
        S1 = self.addHost('S1')
        S2 = self.addHost('S2')
        R1 = self.addHost('R1')
        R2 = self.addHost('R2')

        #TODO: Is this the best method to configure link parameters?
        #10 Mbps 5ms delay 2%loss 1000 packet queue
        #self.addLink(host, switch, bw=10, delay='5ms', loss=2, max_queue_size=1000, use_htb=True)
        #generic_link_options = dict(bw=10, delay='5ms', loss=10, max_queue_size=1000, use_htb=True)

        #TODO: Which links do we need queue/buffer space for?
        #I assume because AR1 and AR2 are the slowest they will need queue space on their links!


        host_AR_bw = Packet_size_bytes * HOST_PACKET_MS * BIT_TO_BYTES
        host_AR_queue = .2 * AR_BR_PACKET_MS * 21
        host_AR_link_options = dict(bw=host_AR_bw, max_queue_size=host_AR_queue)

        AR_BR_bw = Packet_size_bytes * AR_BR_PACKET_MS * BIT_TO_BYTES
        AR_BR_link_options = dict(bw=AR_BR_bw, max_queue_size=host_AR_queue)

        BR_BR_bw = Packet_size_bytes*BR_BR_PACKET_MS*BIT_TO_BYTES
        BR_BR_link_options = dict(bw=AR_BR_bw, delay=BR_BR_DELAY_SHORT)

        #Connect routers to eachother
        #AR1 <-> BR1
        self.addLink(AR1, BR1, **AR_BR_link_options)
        #BR1 <-> BR2
        self.addLink(BR1, BR2, **BR_BR_link_options)
        #AR2 <-> BR2
        self.addLink(AR2, BR2, **AR_BR_link_options)

        #Connect hosts to AR switches
        self.addLink(S1, AR1, **host_AR_link_options)
        self.addLink(S2, AR1, **host_AR_link_options)
        self.addLink(R1, AR2, **host_AR_link_options)
        self.addLink(R2, AR2, **host_AR_link_options)

def simpleTest():

    "Create and test a simple network"
    topo = Dumbbell_topology()
    net = Mininet(topo)
    net.start()
    print( "Dumping host connections" )
    dumpNodeConnections(net.hosts)
    print( "Testing network connectivity" )
    net.pingAll()
    net.stop()

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    simpleTest()
