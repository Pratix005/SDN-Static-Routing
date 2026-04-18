# SDN Static Routing using Ryu Controller + Mininet

**Course:** UE24CS252B – Computer Networks, PES University  
**Project:** SDN Mininet-based Simulation – Static Routing using SDN Controller  
**Controller:** Ryu (OpenFlow 1.3)  
**Emulator:** Mininet  

---

## Problem Statement

Implement static routing paths in a Software-Defined Network using a Ryu controller that **proactively installs flow rules** into OpenFlow switches the moment they connect. Unlike dynamic/reactive controllers, all routes are explicitly defined by the controller — demonstrating full SDN control plane authority over the data plane.

The controller also runs a **background monitor thread** that reinstalls rules every 10 seconds, ensuring routing paths remain unchanged (regression-safe).

---

## Topology

```
h1 (10.0.0.1) --+
                 s1 -------- s2 -------- s3 --+-- h3 (10.0.0.3)
h2 (10.0.0.2) --+                             +-- h4 (10.0.0.4)
```

| Node | IP Address   | MAC Address       | Connected To |
|------|-------------|-------------------|-------------|
| h1   | 10.0.0.1/24 | 00:00:00:00:00:01 | s1 port 1   |
| h2   | 10.0.0.2/24 | 00:00:00:00:00:02 | s1 port 2   |
| h3   | 10.0.0.3/24 | 00:00:00:00:00:03 | s3 port 1   |
| h4   | 10.0.0.4/24 | 00:00:00:00:00:04 | s3 port 2   |
| s1   | dpid=1      | —                 | h1, h2, s2  |
| s2   | dpid=2      | —                 | s1, s3      |
| s3   | dpid=3      | —                 | h3, h4, s2  |

### Port Mapping

| Switch | Port 1 | Port 2 | Port 3 |
|--------|--------|--------|--------|
| s1     | h1     | h2     | s2     |
| s2     | s1     | s3     | —      |
| s3     | h3     | h4     | s2     |

---

## File Structure

```
SDN-Static-Routing/
├── static_routing.py      # Ryu controller – installs static flow rules
├── topology.py            # Mininet topology – 3 switches, 4 hosts
├── regression_test.py     # Regression test – verifies rules persist
└── README.md
```

---

## Design & Implementation

### Controller Logic (`static_routing.py`)

- **Proactive flow installation:** On `EventOFPSwitchFeatures` (switch connect), the controller immediately pushes all flow rules — no waiting for packets.
- **Match-Action rules:** Each rule matches on `eth_type=0x0800` (IPv4) + `ipv4_dst` and outputs to the correct port.
- **ARP handling:** ARP packets are flooded (`OFPP_FLOOD`) so hosts can resolve MACs.
- **Regression monitor:** A background `hub.spawn` thread reinstalls rules every 10 seconds — ensuring static routes persist even if rules are deleted.
- **OpenFlow 1.3:** Uses `OFPFlowMod` with priority, match, and action fields.

### Static Routing Table

**Switch s1 (dpid=1)**
| Priority | Match | Action |
|----------|-------|--------|
| 20 | IPv4 dst=10.0.0.1 | output port 1 (h1) |
| 20 | IPv4 dst=10.0.0.2 | output port 2 (h2) |
| 10 | IPv4 (any) | output port 3 (→ s2) |
| 5  | ARP | FLOOD |

**Switch s2 (dpid=2)**
| Priority | Match | Action |
|----------|-------|--------|
| 20 | IPv4 dst=10.0.0.1 | output port 1 (→ s1) |
| 20 | IPv4 dst=10.0.0.2 | output port 1 (→ s1) |
| 20 | IPv4 dst=10.0.0.3 | output port 2 (→ s3) |
| 20 | IPv4 dst=10.0.0.4 | output port 2 (→ s3) |
| 5  | ARP | FLOOD |

**Switch s3 (dpid=3)**
| Priority | Match | Action |
|----------|-------|--------|
| 20 | IPv4 dst=10.0.0.3 | output port 1 (h3) |
| 20 | IPv4 dst=10.0.0.4 | output port 2 (h4) |
| 10 | IPv4 (any) | output port 3 (→ s2) |
| 5  | ARP | FLOOD |

---

## Setup & Installation

### Prerequisites

```bash
# Mininet
sudo apt install mininet -y

# Open vSwitch
sudo apt install openvswitch-switch -y

# Python 3.10 virtual environment (required — Ryu does not support Python 3.12)
sudo apt install python3.10 python3.10-venv -y
python3.10 -m venv ~/ryu-env
source ~/ryu-env/bin/activate

# Install Ryu with compatible dependencies
pip install pip==21.3.1 setuptools==59.6.0
pip install eventlet==0.30.2 dnspython==1.16.0 six==1.16.0
pip install ryu==4.34
```

### Apply compatibility patches (one time only)

```bash
cat > ~/fix_eventlet.sh << 'EOF'
#!/bin/bash
SITE=~/ryu-env/lib/python3.10/site-packages
sed -i 's/base.is_timeout = property(lambda _: True)/pass  # patched/' $SITE/eventlet/timeout.py
sed -i 's/six.get_function_code(_original_pyio.open),/_original_pyio.open.__func__.__code__,/' $SITE/eventlet/greenio/py3.py
sed -i 's/from eventlet.wsgi import ALREADY_HANDLED/ALREADY_HANDLED = object()/' $SITE/ryu/app/wsgi.py
sed -i 's/collections.MutableMapping/collections.abc.MutableMapping/' $SITE/dns/namedict.py
echo "All patches applied!"
EOF
bash ~/fix_eventlet.sh
```

---

## Execution Steps

### Step 1 — Start Ryu Controller (Terminal 1)

```bash
cd ~/sdn-static-routing
source ~/ryu-env/bin/activate
ryu-manager static_routing.py --observe-links
```

Wait until you see:
```
Static Routing Controller started
```

### Step 2 — Start Mininet Topology (Terminal 2)

```bash
cd ~/Downloads/SDN-Static-Routing-main
sudo python3 topology.py
```

> ⚠️ Never run `sudo mn -c` while Ryu is running — it terminates ryu-manager.

---

## Test Scenarios & Expected Output

### Scenario 1 — Full Connectivity (pingall)

```
mininet> pingall
```

**Expected:**
```
h1 -> h2 h3 h4
h2 -> h1 h3 h4
h3 -> h1 h2 h4
h4 -> h1 h2 h3
*** Results: 0% dropped (12/12 received)
```

### Scenario 2 — Specific Path: h1 → h4

```
mininet> h1 ping -c 4 h4
```

**Expected:**
```
64 bytes from 10.0.0.4: icmp_seq=1 ttl=64 time=0.632 ms
64 bytes from 10.0.0.4: icmp_seq=2 ttl=64 time=0.118 ms
64 bytes from 10.0.0.4: icmp_seq=3 ttl=64 time=0.106 ms
64 bytes from 10.0.0.4: icmp_seq=4 ttl=64 time=0.089 ms
4 packets transmitted, 4 received, 0% packet loss
rtt min/avg/max/mdev = 0.089/0.236/0.632/0.228 ms
```

Path taken: `h1 → s1 (port3) → s2 (port2) → s3 (port2) → h4`

### Scenario 3 — Flow Table Verification

```
mininet> sh ovs-ofctl dump-flows s1 -O OpenFlow13
mininet> sh ovs-ofctl dump-flows s2 -O OpenFlow13
mininet> sh ovs-ofctl dump-flows s3 -O OpenFlow13
```

**Expected (s1):**
```
priority=20,ip,nw_dst=10.0.0.1 actions=output:"s1-eth1"
priority=20,ip,nw_dst=10.0.0.2 actions=output:"s1-eth2"
priority=10,ip actions=output:"s1-eth3"
priority=5,arp actions=FLOOD
```

### Scenario 4 — Throughput Measurement (iperf)

```
mininet> h4 iperf -s &
mininet> h1 iperf -c 10.0.0.4 -t 5
```

### Scenario 5 — Regression Test

Open Terminal 3 while Mininet is still running:

```bash
sudo python3 regression_test.py
```

**Expected:**
```
=== BEFORE: Capturing flow rules ===
s1: 4 rules
s2: 5 rules
s3: 4 rules

=== Deleting all flow rules ===
Deleted rules on s1, s2, s3

Waiting 5s for controller to reinstall rules...

=== AFTER: Capturing flow rules ===
s1: 4 rules
s2: 5 rules
s3: 4 rules

=== Regression Result ===
s1: before=4 rules, after=4 rules → PASS
s2: before=5 rules, after=5 rules → PASS
s3: before=4 rules, after=4 rules → PASS
```

---

## Cleanup

```bash
mininet> exit
sudo mn -c
```

---

## References

1. Ryu SDN Framework Documentation — https://ryu.readthedocs.io/en/latest/
2. Mininet Walkthrough — https://mininet.org/walkthrough/
3. OpenFlow 1.3 Specification — https://opennetworking.org/wp-content/uploads/2014/10/openflow-spec-v1.3.0.pdf
4. Mininet Overview — https://mininet.org/overview/
5. Ryu GitHub — https://github.com/faucetsdn/ryu
6. PES University Course Material — UE24CS252B Computer Networks
