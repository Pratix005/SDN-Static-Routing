## Problem Statement
Implement static routing paths using controller-installed OpenFlow flow rules in a Mininet SDN environment. All forwarding paths are pre-defined in the Ryu controller — no dynamic learning.

## Topology
h1 (10.0.0.1) ─┐

s1 ── s2 ── s3 ─┬─ h3 (10.0.0.3)

h2 (10.0.0.2) ─┘               └─ h4 (10.0.0.4)

- 4 hosts, 3 switches (linear)
- Controller: Ryu (OpenFlow 1.3)

## Setup & Execution

### Install
```bash
sudo apt install mininet python3.9 python3.9-venv -y
python3.9 -m venv ~/ryu-env
source ~/ryu-env/bin/activate
pip install setuptools==67.6.0
pip install ryu eventlet==0.30.2
```

### Run (2 terminals)
```bash
# Terminal 1 — Ryu controller
source ~/ryu-env/bin/activate
ryu-manager static_routing.py --verbose

# Terminal 2 — Mininet topology
sudo python3 topology.py
```

## Test Scenarios

### Scenario 1 — Full connectivity

mininet> pingall
Results: 0% dropped (12/12 received)

### Scenario 2 — Cross-switch ping
mininet> h1 ping -c 4 10.0.0.3
0% packet loss, rtt avg = 0.283ms
mininet> h2 ping -c 4 10.0.0.4
0% packet loss, rtt avg = 0.182ms

### Scenario 3 — Throughput (iperf)
mininet> h3 iperf -s &
mininet> h1 iperf -c 10.0.0.3 -t 5
Bandwidth: 29.7 Gbits/sec

### Scenario 4 — Flow table inspection
```bash
sudo ovs-ofctl dump-flows s1
sudo ovs-ofctl dump-flows s2
sudo ovs-ofctl dump-flows s3
```

## Regression Test
```bash
sudo python3 regression_test.py
# Expected: s1 PASS, s2 PASS, s3 PASS
```
Rules are identical before and after deletion + reinstall.

## References
- https://ryu.readthedocs.io/
- https://mininet.org/walkthrough/
- https://opennetworking.org/wp-content/uploads/2014/10/openflow-spec-v1.3.0.pdf

## Routing Behavior

All paths are statically defined — no dynamic learning occurs.

| Source | Destination | Path |
|--------|-------------|------|
| h1 | h3 | h1 → s1(eth1) → s1(eth3) → s2(eth1) → s2(eth2) → s3(eth3) → s3(eth1) → h3 |
| h1 | h4 | h1 → s1 → s2 → s3(eth2) → h4 |
| h2 | h3 | h2 → s1(eth2) → s2 → s3 → h3 |
| h2 | h4 | h2 → s1 → s2 → s3 → h4 |
| h1 | h2 | h1 → s1(eth1) → s1(eth2) → h2 (stays on s1) |

### Flow Rule Logic
- **s1**: dst=10.0.0.1 → port1, dst=10.0.0.2 → port2, all other IP → port3 (to s2)
- **s2**: dst=10.0.0.1/2 → port1 (back to s1), dst=10.0.0.3/4 → port2 (to s3)
- **s3**: dst=10.0.0.3 → port1, dst=10.0.0.4 → port2, all other IP → port3 (to s2)
