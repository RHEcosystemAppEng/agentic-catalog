#!/usr/bin/env python3
"""Fetch Red Hat CSAF VEX data for a given CVE.

Default mode: returns a structured summary of the VEX data — all products with
their CPEs, component names, statuses, remediations, justifications, and severity.
No interpretation or filtering — just the full VEX content in a readable format.

With --raw: returns the complete raw CSAF VEX JSON document.
"""

import argparse
import json
import re
import sys

import requests

VEX_API = "https://security.access.redhat.com/data/csaf/v2/vex/{year}/{cve_id_lower}.json"
TIMEOUT = 15


def fetch_vex(cve_id):
    year = cve_id.split("-")[1]
    url = VEX_API.format(year=year, cve_id_lower=cve_id.lower())
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 404:
            return None, 404, []
        if resp.status_code != 200:
            return None, resp.status_code, [f"HTTP {resp.status_code}"]
        return resp.json(), 200, []
    except requests.RequestException as e:
        return None, 0, [f"Request failed: {e}"]
    except ValueError as e:
        return None, 0, [f"JSON parse error: {e}"]


def build_product_map(vex_data):
    """Build map: product_id -> {full_name, cpe, component_name} from branches."""
    product_map = {}
    tree = vex_data.get("product_tree", {})

    for branch in tree.get("branches", []):
        _walk_branches(branch, product_map)

    for rel in tree.get("relationships", []):
        fpn = rel.get("full_product_name", {})
        pid = fpn.get("product_id", "")
        name = fpn.get("name", "")
        parent_pid = rel.get("relates_to_product_reference", "")
        component_pid = rel.get("product_reference", "")

        parent_info = product_map.get(parent_pid, {})
        parent_cpe = parent_info.get("cpe", "")

        comp_info = product_map.get(component_pid, {})
        comp_name = comp_info.get("name", component_pid)

        product_map[pid] = {
            "full_name": name,
            "cpe": parent_cpe,
            "component": comp_name,
            "parent_product": parent_pid,
        }

    return product_map


def _walk_branches(branch, product_map):
    fpn = branch.get("product", {})
    if fpn:
        pid = fpn.get("product_id", "")
        name = fpn.get("name", "")
        cpe = ""
        helper = fpn.get("product_identification_helper", {})
        if isinstance(helper, dict):
            cpe = helper.get("cpe", "")
        product_map[pid] = {"name": name, "cpe": cpe, "full_name": name}

    for sub in branch.get("branches", []):
        _walk_branches(sub, product_map)


def extract_summary(vex_data, product_map):
    """Extract a structured summary of all VEX entries — no filtering."""
    products = []

    for vuln in vex_data.get("vulnerabilities", []):
        cve = vuln.get("cve", "")

        # Severity
        severity = ""
        for threat in vuln.get("threats", []):
            if threat.get("category") == "impact":
                severity = threat.get("details", "")
                break

        # Remediations: product_id -> {category, details, url}
        remediation_map = {}
        for rem in vuln.get("remediations", []):
            for pid in rem.get("product_ids", []):
                remediation_map.setdefault(pid, []).append({
                    "category": rem.get("category", ""),
                    "details": rem.get("details", ""),
                    "url": rem.get("url", ""),
                })

        # Flags: product_id -> justification label
        flag_map = {}
        for flag in vuln.get("flags", []):
            for pid in flag.get("product_ids", []):
                flag_map[pid] = flag.get("label", "")

        # Walk product_status groups
        for status_key, pids in vuln.get("product_status", {}).items():
            for pid in pids:
                info = product_map.get(pid, {})
                entry = {
                    "product_id": pid,
                    "full_name": info.get("full_name", ""),
                    "cpe": info.get("cpe", ""),
                    "component": info.get("component", ""),
                    "status": status_key,
                }

                if pid in flag_map:
                    entry["justification"] = flag_map[pid]

                if pid in remediation_map:
                    entry["remediations"] = remediation_map[pid]

                products.append(entry)

        # Deduplicate: collapse arch variants and sub-packages into one entry per base package + CPE + status
        deduped = {}
        for p in products:
            comp = p.get("component", "")
            # Strip version-release and arch from component: "podman-6:5.6.0-14.el9_7.x86_64" -> "podman"
            base_comp = re.split(r'-\d+:', comp)[0] if re.search(r'-\d+:', comp) else comp
            base_comp = re.sub(r'\.(x86_64|aarch64|ppc64le|s390x|noarch|src|i686)$', '', base_comp)
            # Strip sub-package suffixes: podman-debuginfo -> podman, podman-tests -> podman
            base_comp = re.sub(r'-(debuginfo|debugsource|tests-debuginfo|tests|remote-debuginfo|remote|plugins-debuginfo|plugins|docker|catatonit|gvproxy|manpages|src)$', '', base_comp)
            key = (base_comp, p["cpe"], p["status"])
            if key not in deduped:
                deduped[key] = p.copy()
                deduped[key]["base_package"] = base_comp
                deduped[key]["sub_packages"] = 1
            else:
                deduped[key]["sub_packages"] += 1

        return {"cve": cve, "severity": severity, "products": list(deduped.values())}

    return {"cve": "", "severity": "", "products": []}


def detect_blanket_vex(products):
    under_inv = [p for p in products if p["status"] == "under_investigation"]
    return len(under_inv) > 20


def main():
    parser = argparse.ArgumentParser(description="Fetch Red Hat VEX data")
    parser.add_argument("cve_id", help="CVE identifier (e.g., CVE-2024-45490)")
    parser.add_argument("--raw", action="store_true", help="Return full raw CSAF VEX JSON")
    args = parser.parse_args()

    cve_id = args.cve_id.upper()
    if not re.match(r"^CVE-\d{4}-\d+$", cve_id):
        json.dump({"cve_id": args.cve_id, "error": "Invalid CVE ID format"}, sys.stdout, indent=2)
        sys.exit(1)

    vex_data, http_status, errors = fetch_vex(cve_id)

    if vex_data is None:
        json.dump({
            "cve_id": cve_id,
            "http_status": http_status,
            "vex": None,
            "products": [],
            "errors": errors if errors else [f"No VEX file (HTTP {http_status})"],
        }, sys.stdout, indent=2)
        print()
        sys.exit(0 if http_status == 404 else 1)

    if args.raw:
        json.dump({
            "cve_id": cve_id,
            "http_status": 200,
            "vex": vex_data,
            "errors": [],
        }, sys.stdout, indent=2)
        print()
        return

    product_map = build_product_map(vex_data)
    summary = extract_summary(vex_data, product_map)
    is_blanket = detect_blanket_vex(summary.get("products", []))

    result = {
        "cve_id": cve_id,
        "http_status": 200,
        "severity": summary["severity"],
        "is_blanket_vex": is_blanket,
        "total_products": len(summary["products"]),
        "products": summary["products"],
        "errors": [],
    }

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
