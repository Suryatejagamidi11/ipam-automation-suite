"""
run_all.py

Runs the full IPAM toolkit against the sample dataset in one pass:
utilization report -> conflict/stale scan -> re-IP migration plan.

Usage:
    python src/run_all.py
"""

from ipam_client import IPAMClient
import subnet_utilization
import conflict_detector
import reip_simulator
from pathlib import Path


def main():
    client = IPAMClient(mode="sample")
    subnets = client.get_networks()

    print("\n" + "#" * 70)
    print("# 1. SUBNET UTILIZATION")
    print("#" * 70)
    report = subnet_utilization.build_report(subnets)
    subnet_utilization.print_report(report)

    print("\n" + "#" * 70)
    print("# 2. CONFLICT & STALE RESERVATION SCAN")
    print("#" * 70)
    duplicates = conflict_detector.find_duplicate_ips(subnets)
    stale = conflict_detector.find_stale_reservations(subnets)
    conflict_detector.print_findings(duplicates, stale)

    print("\n" + "#" * 70)
    print("# 3. RE-IP MIGRATION PLAN (sample: legacy HPE range)")
    print("#" * 70)
    legacy_subnet = next(s for s in subnets if s["network"] == "172.16.5.0/24")
    plan = reip_simulator.plan_reip(legacy_subnet, "10.50.5.0/24")
    output_dir = Path(__file__).resolve().parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)
    reip_simulator.generate_markdown_plan(plan, str(output_dir / "reip_migration_plan.md"))

    print("\nDone. Full re-IP plan saved to reports/reip_migration_plan.md\n")


if __name__ == "__main__":
    main()
