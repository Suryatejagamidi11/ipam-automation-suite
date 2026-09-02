# IPAM Automation Suite

A Python toolkit for automating common IP Address Management (IPAM) operations at scale: utilization reporting, conflict detection, and re-IP migration planning.

Built to reflect real enterprise IPAM operations — managing utilization and conflicts across hundreds of networks, and planning renumbering projects during network separations or acquisitions.

## Why this exists

Managing IP space manually across dozens or hundreds of subnets doesn't scale. Three problems come up constantly in real IPAM operations:

1. **Which subnets are about to run out of addresses** (and which are sitting mostly empty, wasting allocated space)
2. **Duplicate or stale IP assignments** that cause outages or block address reclamation
3. **Planning a re-IP / renumbering migration** — mapping old addresses to new ones, generating a documented migration and rollback plan before touching production

This toolkit automates all three.

## Features

- **Subnet Utilization Report** — flags subnets nearing exhaustion (default: ≥85% used) and underutilized subnets that are reclamation candidates (default: ≤10% used)
- **Conflict Detector** — finds duplicate IP assignments across the environment and flags stale/decommissioned reservations still holding addresses
- **Re-IP Migration Planner** — maps hosts from a source subnet to a target subnet, checks target capacity, and auto-generates a Markdown migration + rollback plan
- **Pluggable data source** — runs against included sample data out of the box, or against a live Infoblox grid via WAPI by setting environment variables (no code changes needed)

## Quick start

```bash
git clone https://github.com/<your-username>/ipam-automation-suite.git
cd ipam-automation-suite
pip install -r requirements.txt

# Run everything against the included sample dataset
python src/run_all.py
```

This runs all three tools against `sample_data/subnets.json` — a small mock dataset (no real credentials or infrastructure needed) — so you can see exactly what the output looks like.

### Run tools individually

```bash
python src/subnet_utilization.py    # utilization report
python src/conflict_detector.py     # duplicate / stale IP scan
python src/reip_simulator.py        # generates reports/reip_migration_plan.md
```

## Using it against a real Infoblox grid

Set these environment variables and switch the client mode to `"infoblox"` in your script:

```bash
export INFOBLOX_HOST="gridmaster.example.com"
export INFOBLOX_USER="your-api-user"
export INFOBLOX_PASS="your-api-password"
```

```python
from ipam_client import IPAMClient
client = IPAMClient(mode="infoblox")
subnets = client.get_networks()
```

> **Note:** at large scale (hundreds of networks) you'll want to add pagination (`_max_results` / `_page_id`) to `_get_networks_infoblox()` in `src/ipam_client.py`, since the WAPI caps results per request by default.

## Sample output

**Utilization report:**
```
⚠  NEAR EXHAUSTION (>= 85.0% used):
   10.10.0.0/24          97.6%  (248/254)  R&D Lab - Building A
   192.168.100.0/28     100.0%  (14/14)   AWS us-east-1 VPC - Management Subnet

♻  UNDERUTILIZED (<= 10.0% used, reclamation candidates):
   10.10.1.0/24           4.7%  (12/254)  R&D Lab - Building B
```

**Re-IP migration plan** (auto-generated, see `reports/reip_migration_plan.md` after running):
- IP mapping table (old → new)
- Step-by-step migration checklist
- Step-by-step rollback plan

## Project structure

```
ipam-automation-suite/
├── src/
│   ├── ipam_client.py          # data source abstraction (sample data or Infoblox WAPI)
│   ├── subnet_utilization.py   # utilization report
│   ├── conflict_detector.py    # duplicate/stale IP scan
│   ├── reip_simulator.py       # re-IP migration planner
│   └── run_all.py              # runs all three in sequence
├── sample_data/
│   └── subnets.json            # mock dataset for demo/testing
├── reports/                     # generated migration plans land here
├── requirements.txt
└── README.md
```

## Roadmap / possible extensions

- [ ] Add pagination support for large Infoblox grids
- [ ] Export utilization reports to CSV/Excel
- [ ] Slack/email alerting when a subnet crosses the exhaustion threshold
- [ ] IPv6 support in the re-IP planner
- [ ] Integration with a config management tool (Ansible) to push DNS/DHCP changes directly from a generated migration plan

## Background

Built by a network engineer with hands-on experience managing IP address space across large multi-site environments (250K+ IPs, 280+ networks) during a company separation and cloud migration project. This toolkit reflects the type of automation used to make that kind of operation manageable.
