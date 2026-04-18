#!/usr/bin/env python3
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink
import time

def build_topo():
    net = Mininet(switch=OVSSwitch, controller=None, link=TCLink, autoSetMacs=True)

    # Use port 6633 (Ryu default)
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)

    # Force OpenFlow 1.3 on all switches
    s1 = net.addSwitch('s1', protocols='OpenFlow13')
    s2 = net.addSwitch('s2', protocols='OpenFlow13')
    s3 = net.addSwitch('s3', protocols='OpenFlow13')

    h1 = net.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
    h2 = net.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
    h3 = net.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
    h4 = net.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')

    # Port mapping after these links:
    # s1: port1=h1, port2=h2, port3=s2
    # s2: port1=s1, port2=s3
    # s3: port1=h3, port2=h4, port3=s2
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s3)
    net.addLink(h4, s3)
    net.addLink(s1, s2)
    net.addLink(s2, s3)

    net.start()
    print("=== Topology started. Waiting for controller...")
    time.sleep(3)
    print("=== Ready! Try: pingall, h1 ping -c4 h4, iperf h1 h4")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    build_topo()
