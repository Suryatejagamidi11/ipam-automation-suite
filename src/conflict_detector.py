"""
conflict_detector.py

Scans all subnets for:
  - Duplicate IP assignments (same IP assigned to more than one host record)
  - Decommissioned hosts still holding an active-looking IP reservation

At scale (hundreds of networks, tens of thousands of hosts), duplicate or
stale records are one of the most common sources of real outages -- two
devices fighting over the same address, or "phantom" reservations blocking
addresses that should have been freed after a decommission.
"""

from typing import List, Dict, Any
from collections import defaultdict
from ipam_client import IPAMClient


def find_duplicate_ips(subnets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ip_to_hosts = defaultdict(list)

    for subnet in subnets:
        for record in subnet.get("assigned", []):
            key = record["ip"]
            ip_to_hosts[key].append({
                "network": subnet["network"],
                "site": subnet.get("site", ""),
                "host": record.get("host"),
                "status": record.get("status"),
            })

    duplicates = []
    for ip, hosts in ip_to_hosts.items():
        if len(hosts) > 1:
            duplicates.append({"ip": ip, "conflicting_records": hosts})

    return duplicates


def find_stale_reservations(subnets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    stale = []
    for subnet in subnets:
        for record in subnet.get("assigned", []):
            if record.get("status") == "decommissioned":
                stale.append({
                    "network": subnet["network"],
                    "site": subnet.get("site", ""),
                    "ip": record["ip"],
                    "host": record.get("host"),
                })
    return stale


def print_findings(duplicates: List[Dict[str, Any]], stale: List[Dict[str, Any]]) -> None:
    print("=" * 70)
    print("IP CONFLICT & STALE RESERVATION REPORT")
    print("=" * 70)

    print(f"\n🚨 DUPLICATE IP ASSIGNMENTS: {len(duplicates)} found")
    for dup in duplicates:
        print(f"   {dup['ip']}:")
        for rec in dup["conflicting_records"]:
            print(f"      -> {rec['host']:<20} in {rec['network']} ({rec['site']}) [{rec['status']}]")

    print(f"\n🗑  STALE / DECOMMISSIONED RESERVATIONS: {len(stale)} found")
    for s in stale:
        print(f"   {s['ip']:<16} {s['host']:<20} {s['network']} ({s['site']}) "
              f"-- can likely be reclaimed")


if __name__ == "__main__":
    client = IPAMClient(mode="sample")
    subnets = client.get_networks()
    duplicates = find_duplicate_ips(subnets)
    stale = find_stale_reservations(subnets)
    print_findings(duplicates, stale)
