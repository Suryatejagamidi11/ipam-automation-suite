"""
ipam_client.py

A thin abstraction layer for pulling subnet/IP data from an IPAM source.

Two modes:
  - "sample": reads from sample_data/subnets.json (no credentials needed, safe for demos/portfolio)
  - "infoblox": pulls live data from an Infoblox WAPI endpoint (requires env vars)

This mirrors how you'd structure a real automation tool: keep the data source
swappable so the reporting/analysis logic never has to change when you point
it at a real grid vs. a lab/demo dataset.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any

import requests


class IPAMClient:
    def __init__(self, mode: str = "sample", sample_path: str = None):
        self.mode = mode
        self.sample_path = sample_path or str(
            Path(__file__).resolve().parent.parent / "sample_data" / "subnets.json"
        )

        # Infoblox WAPI config - only used when mode="infoblox"
        self.grid_host = os.environ.get("INFOBLOX_HOST")
        self.username = os.environ.get("INFOBLOX_USER")
        self.password = os.environ.get("INFOBLOX_PASS")
        self.wapi_version = os.environ.get("INFOBLOX_WAPI_VERSION", "v2.12")

    def get_networks(self) -> List[Dict[str, Any]]:
        if self.mode == "sample":
            return self._load_sample()
        elif self.mode == "infoblox":
            return self._get_networks_infoblox()
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def _load_sample(self) -> List[Dict[str, Any]]:
        with open(self.sample_path, "r") as f:
            return json.load(f)

    def _get_networks_infoblox(self) -> List[Dict[str, Any]]:
        """
        Pulls network objects from Infoblox WAPI.
        Requires INFOBLOX_HOST, INFOBLOX_USER, INFOBLOX_PASS env vars set.

        NOTE: This returns raw Infoblox network objects. In production you'd
        add pagination (_max_results / _page_id) for large grids -- at 282+
        networks you will hit the default result cap.
        """
        if not all([self.grid_host, self.username, self.password]):
            raise EnvironmentError(
                "Missing Infoblox credentials. Set INFOBLOX_HOST, INFOBLOX_USER, "
                "INFOBLOX_PASS environment variables, or use mode='sample' for a demo run."
            )

        url = f"https://{self.grid_host}/wapi/{self.wapi_version}/network"
        params = {
            "_return_fields": "network,comment,extattrs,network_view",
            "_max_results": 1000,
        }

        response = requests.get(
            url,
            auth=(self.username, self.password),
            params=params,
            verify=True,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
