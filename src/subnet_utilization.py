"""
subnet_utilization.py

Generates a utilization report across all managed subnets:
  - percent utilized
  - subnets nearing exhaustion (default threshold: 85%)
  - subnets that are significantly underutilized (candidates for reclamation)

This is the kind of report that matters at scale -- when you're managing
hundreds of networks, you can't eyeball which ones are about to run out
of addresses or which ones are sitting mostly empty and wasting allocated
space that could be reclaimed elsewhere.
"""

from typing import List, Dict, Any
from ipam_client import IPAMClient


HIGH_UTILIZATION_THRESHOLD = 85.0
LOW_UTILIZATION_THRESHOLD = 10.0


def calculate_utilization(subnet: Dict[str, Any]) -> float:
    total = subnet.get("total_ips", 0)
    used = subnet.get("used_ips", 0)
    if total == 0:
        return 0.0
    return round((used / total) * 100, 1)


def build_report(subnets: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    near_exhaustion = []
    underutilized = []

    for subnet in subnets:
        pct = calculate_utilization(subnet)
        row = {
            "network": subnet["network"],
            "description": subnet.get("description", ""),
            "site": subnet.get("site", ""),
            "utilization_pct": pct,
            "used_ips": subnet.get("used_ips", 0),
            "total_ips": subnet.get("total_ips", 0),
        }
        rows.append(row)

        if pct >= HIGH_UTILIZATION_THRESHOLD:
            near_exhaustion.append(row)
        elif pct <= LOW_UTILIZATION_THRESHOLD:
            underutilized.append(row)

    rows.sort(key=lambda r: r["utilization_pct"], reverse=True)

    return {
        "total_subnets": len(subnets),
        "near_exhaustion": near_exhaustion,
        "underutilized": underutilized,
        "all_subnets": rows,
    }


def print_report(report: Dict[str, Any]) -> None:
    print("=" * 70)
    print("SUBNET UTILIZATION REPORT")
    print("=" * 70)
    print(f"Total subnets analyzed: {report['total_subnets']}\n")

    print(f"⚠  NEAR EXHAUSTION (>= {HIGH_UTILIZATION_THRESHOLD}% used):")
    if report["near_exhaustion"]:
        for r in report["near_exhaustion"]:
            print(f"   {r['network']:<20} {r['utilization_pct']:>5}%  "
                  f"({r['used_ips']}/{r['total_ips']})  {r['description']}")
    else:
        print("   None")

    print(f"\n♻  UNDERUTILIZED (<= {LOW_UTILIZATION_THRESHOLD}% used, reclamation candidates):")
    if report["underutilized"]:
        for r in report["underutilized"]:
            print(f"   {r['network']:<20} {r['utilization_pct']:>5}%  "
                  f"({r['used_ips']}/{r['total_ips']})  {r['description']}")
    else:
        print("   None")

    print("\n" + "-" * 70)
    print("ALL SUBNETS (sorted by utilization)")
    print("-" * 70)
    for r in report["all_subnets"]:
        print(f"   {r['network']:<20} {r['utilization_pct']:>5}%  "
              f"({r['used_ips']}/{r['total_ips']})  {r['site']}")


if __name__ == "__main__":
    client = IPAMClient(mode="sample")
    subnets = client.get_networks()
    report = build_report(subnets)
    print_report(report)
