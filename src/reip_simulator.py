"""
reip_simulator.py

Simulates a subnet re-IP (renumbering) migration -- e.g. moving a network
off a legacy address space onto a new one, the kind of work involved in
separating IP space after an acquisition/divestiture.

Given a source subnet and a target subnet, it:
  1. Maps every existing host to a new IP in the target range (preserving order)
  2. Flags any capacity mismatch (target too small for source host count)
  3. Generates a step-by-step migration + rollback plan as a Markdown file

This does NOT touch real infrastructure -- it's a planning/simulation tool.
In a real migration you'd feed its output into your change management
process and your actual config push (Ansible/Netmiko) separately.
"""

import ipaddress
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from ipam_client import IPAMClient


def plan_reip(subnet: Dict[str, Any], target_cidr: str) -> Dict[str, Any]:
    target_network = ipaddress.ip_network(target_cidr, strict=False)
    target_hosts = list(target_network.hosts())

    assigned = subnet.get("assigned", [])
    active_hosts = [r for r in assigned if r.get("status") == "active"]

    capacity_ok = len(target_hosts) >= len(active_hosts)

    mappings = []
    for i, record in enumerate(active_hosts):
        new_ip = str(target_hosts[i]) if i < len(target_hosts) else None
        mappings.append({
            "host": record.get("host"),
            "old_ip": record["ip"],
            "new_ip": new_ip,
        })

    return {
        "source_network": subnet["network"],
        "target_network": target_cidr,
        "site": subnet.get("site", ""),
        "capacity_ok": capacity_ok,
        "hosts_to_migrate": len(active_hosts),
        "target_capacity": len(target_hosts),
        "mappings": mappings,
    }


def generate_markdown_plan(plan: Dict[str, Any], output_path: str) -> None:
    lines = []
    lines.append(f"# Re-IP Migration Plan: {plan['source_network']} -> {plan['target_network']}")
    lines.append("")
    lines.append(f"**Site:** {plan['site']}  ")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ")
    lines.append(f"**Hosts to migrate:** {plan['hosts_to_migrate']}  ")
    lines.append(f"**Target capacity:** {plan['target_capacity']} usable addresses  ")

    if not plan["capacity_ok"]:
        lines.append("")
        lines.append("> ⚠️ **WARNING:** Target subnet does NOT have enough capacity for all "
                      "active hosts. Choose a larger CIDR before proceeding.")

    lines.append("")
    lines.append("## IP Mapping")
    lines.append("")
    lines.append("| Host | Old IP | New IP |")
    lines.append("|------|--------|--------|")
    for m in plan["mappings"]:
        new_ip = m["new_ip"] if m["new_ip"] else "**NO CAPACITY**"
        lines.append(f"| {m['host']} | {m['old_ip']} | {new_ip} |")

    lines.append("")
    lines.append("## Migration Steps")
    lines.append("")
    lines.append("1. Create the new subnet/VLAN in IPAM and on switching infrastructure.")
    lines.append("2. Update DHCP scope or static assignments per the mapping table above.")
    lines.append("3. Update DNS records (A/PTR) for each host to the new IP.")
    lines.append("4. Update firewall rules, ACLs, and any hardcoded IP references "
                  "(monitoring tools, load balancer pools, etc.).")
    lines.append("5. Cut over hosts in maintenance window; verify connectivity per host.")
    lines.append("6. Monitor for 24-48h before decommissioning old subnet.")
    lines.append("7. Reclaim old subnet in IPAM once confirmed clear.")

    lines.append("")
    lines.append("## Rollback Plan")
    lines.append("")
    lines.append("1. Revert DNS records to original IPs (keep old subnet active until "
                  "cutover is confirmed stable).")
    lines.append("2. Revert DHCP scope / static assignments to old subnet.")
    lines.append("3. Revert firewall/ACL changes tied to the new subnet.")
    lines.append("4. Do not deactivate the old subnet in IPAM until rollback window "
                  "has fully closed.")

    Path(output_path).write_text("\n".join(lines))
    print(f"Migration plan written to: {output_path}")


if __name__ == "__main__":
    client = IPAMClient(mode="sample")
    subnets = client.get_networks()

    # Example: re-IP the legacy HPE range onto a new company-standard range
    legacy_subnet = next(s for s in subnets if s["network"] == "172.16.5.0/24")
    plan = plan_reip(legacy_subnet, "10.50.5.0/24")

    output_dir = Path(__file__).resolve().parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)
    generate_markdown_plan(plan, str(output_dir / "reip_migration_plan.md"))
