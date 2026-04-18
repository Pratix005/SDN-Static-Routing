#!/usr/bin/env python3
import subprocess, time

switches = ['s1', 's2', 's3']

def dump_flows(sw):
    result = subprocess.run(['sudo', 'ovs-ofctl', 'dump-flows', sw], capture_output=True, text=True)
    return result.stdout

def del_flows(sw):
    subprocess.run(['sudo', 'ovs-ofctl', 'del-flows', sw], capture_output=True)

print("=== BEFORE: Capturing flow rules ===")
before = {sw: dump_flows(sw) for sw in switches}
for sw, rules in before.items():
    count = rules.count('priority')
    print(f"{sw}: {count} rules")

print("\n=== Deleting all flow rules ===")
for sw in switches:
    del_flows(sw)
    print(f"Deleted rules on {sw}")

print("\nWaiting 5s for controller to reinstall rules...")
time.sleep(5)

print("\n=== AFTER: Capturing flow rules ===")
after = {sw: dump_flows(sw) for sw in switches}
for sw, rules in after.items():
    count = rules.count('priority')
    print(f"{sw}: {count} rules")

print("\n=== Regression Result ===")
for sw in switches:
    b = before[sw].count('priority')
    a = after[sw].count('priority')
    status = "PASS" if b == a else "FAIL"
    print(f"{sw}: before={b} rules, after={a} rules → {status}")
