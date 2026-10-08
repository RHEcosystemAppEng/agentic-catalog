#!/usr/bin/env python3
"""Fetch Red Hat Security Advisory (RHSA) CSAF data and extract CVE references."""

import argparse
import json
import re
import sys

import requests

ADVISORY_API = "https://security.access.redhat.com/data/csaf/v2/advisories/{year}/{advisory_id_normalized}.json"
TIMEOUT = 15

RHSA_RE = re.compile(r"^RHSA-(\d{4})[:\-](\d+)$", re.IGNORECASE)


def normalize_advisory_id(raw_id):
    """Normalize RHSA-YYYY:NNNNN or RHSA-YYYY-NNNNN to the URL format (underscore)."""
    match = RHSA_RE.match(raw_id)
    if not match:
        return None, None, f"Invalid advisory ID format: '{raw_id}'. Expected: RHSA-YYYY:NNNNN"
    year = match.group(1)
    seq = match.group(2)
    normalized = f"rhsa-{year}_{seq}"
    return normalized, year, None


def fetch_advisory(advisory_id):
    normalized, year, err = normalize_advisory_id(advisory_id)
    if err:
        return None, 0, [err]

    url = ADVISORY_API.format(year=year, advisory_id_normalized=normalized)
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 404:
            return None, 404, [f"Advisory not found: {advisory_id}"]
        if resp.status_code != 200:
            return None, resp.status_code, [f"HTTP {resp.status_code} fetching advisory"]
        return resp.json(), 200, []
    except requests.RequestException as e:
        return None, 0, [f"Request failed: {e}"]
    except ValueError as e:
        return None, 0, [f"JSON parse error: {e}"]


def extract_cves(advisory_data):
    cves = []
    for vuln in advisory_data.get("vulnerabilities", []):
        cve_id = vuln.get("cve", "")
        if not cve_id:
            continue

        title = vuln.get("title", "")

        severity = ""
        base_score = ""
        for score_entry in vuln.get("scores", []):
            cvss = score_entry.get("cvss_v3", {})
            if cvss:
                severity = cvss.get("baseSeverity", "")
                base_score = str(cvss.get("baseScore", ""))
                break

        cves.append({
            "cve_id": cve_id,
            "title": title,
            "severity": severity,
            "cvss_score": base_score,
        })

    return cves


def extract_advisory_metadata(advisory_data):
    doc = advisory_data.get("document", {})
    tracking = doc.get("tracking", {})
    agg_sev = doc.get("aggregate_severity", {})

    return {
        "advisory_id": tracking.get("id", ""),
        "title": doc.get("title", ""),
        "initial_release_date": tracking.get("initial_release_date", ""),
        "current_release_date": tracking.get("current_release_date", ""),
        "aggregate_severity": agg_sev.get("text", ""),
    }


def extract_fixed_packages(advisory_data):
    packages = []
    tree = advisory_data.get("product_tree", {})

    product_map = {}
    for rel in tree.get("relationships", []):
        fpn = rel.get("full_product_name", {})
        pid = fpn.get("product_id", "")
        name = fpn.get("name", "")
        parent = rel.get("relates_to_product_reference", "")
        product_map[pid] = {"name": name, "parent": parent}

    for vuln in advisory_data.get("vulnerabilities", []):
        status_groups = vuln.get("product_status", {})
        fixed_pids = status_groups.get("fixed", [])
        cve_id = vuln.get("cve", "")

        for pid in fixed_pids:
            info = product_map.get(pid, {})
            if info:
                packages.append({
                    "product_id": pid,
                    "name": info.get("name", ""),
                    "cve_id": cve_id,
                })

    return packages


def main():
    parser = argparse.ArgumentParser(description="Fetch Red Hat Security Advisory and extract CVEs")
    parser.add_argument("advisory_id", help="Advisory ID (e.g., RHSA-2026:3337)")
    parser.add_argument("--include-packages", action="store_true",
                        help="Include list of fixed packages from product_tree")
    args = parser.parse_args()

    advisory_data, http_status, errors = fetch_advisory(args.advisory_id)

    if advisory_data is None:
        result = {
            "advisory_id": args.advisory_id,
            "http_status": http_status,
            "metadata": {},
            "cves": [],
            "errors": errors,
        }
        json.dump(result, sys.stdout, indent=2)
        print()
        sys.exit(0 if http_status == 404 else 1)

    metadata = extract_advisory_metadata(advisory_data)
    cves = extract_cves(advisory_data)

    result = {
        "advisory_id": metadata["advisory_id"] or args.advisory_id.upper(),
        "http_status": http_status,
        "metadata": metadata,
        "cves": cves,
        "cve_ids": [c["cve_id"] for c in cves],
        "cve_count": len(cves),
        "errors": errors,
    }

    if args.include_packages:
        result["fixed_packages"] = extract_fixed_packages(advisory_data)

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
