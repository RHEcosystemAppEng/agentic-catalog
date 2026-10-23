#!/usr/bin/env python3
"""Fetch CVE metadata from MITRE, OSV.dev, and Go vulnerability database."""

import argparse
import json
import re
import sys

import requests

MITRE_API = "https://cveawg.mitre.org/api/cve/{cve_id}"
OSV_API = "https://api.osv.dev/v1/vulns/{cve_id}"
GO_VULN_DB = "https://vuln.go.dev/ID/{go_id}.json"
TIMEOUT = 15


def fetch_mitre(cve_id):
    affected = []
    description = ""
    errors = []
    try:
        resp = requests.get(MITRE_API.format(cve_id=cve_id), timeout=TIMEOUT)
        if resp.status_code == 404:
            errors.append(f"MITRE: CVE {cve_id} not found (404)")
            return affected, description, errors
        if resp.status_code != 200:
            errors.append(f"MITRE: HTTP {resp.status_code}")
            return affected, description, errors

        data = resp.json()
        cna = data.get("containers", {}).get("cna", {})

        descs = cna.get("descriptions", [])
        for d in descs:
            if d.get("lang", "").startswith("en"):
                description = d.get("value", "")
                break
        if not description and descs:
            description = descs[0].get("value", "")

        for entry in cna.get("affected", []):
            product = entry.get("product", "")
            vendor = entry.get("vendor", "")
            ecosystem = _guess_ecosystem(entry)

            for ver_block in entry.get("versions", []):
                version_info = {}
                status = ver_block.get("status", "")
                if status == "affected":
                    version_info["introduced"] = ver_block.get("version", "")
                    less_than = ver_block.get("lessThan", "")
                    less_equal = ver_block.get("lessThanOrEqual", "")
                    if less_than:
                        version_info["fixed"] = less_than
                    elif less_equal:
                        version_info["last_affected"] = less_equal

                affected.append({
                    "ecosystem": ecosystem,
                    "package": product,
                    "vendor": vendor,
                    "versions": version_info,
                    "source": "mitre",
                })

            if not entry.get("versions"):
                affected.append({
                    "ecosystem": ecosystem,
                    "package": product,
                    "vendor": vendor,
                    "versions": {},
                    "source": "mitre",
                })

    except requests.RequestException as e:
        errors.append(f"MITRE: request failed: {e}")
    except (KeyError, ValueError) as e:
        errors.append(f"MITRE: parse error: {e}")

    return affected, description, errors


def fetch_osv(cve_id):
    affected = []
    aliases = []
    errors = []
    go_ids = []
    try:
        resp = requests.get(OSV_API.format(cve_id=cve_id), timeout=TIMEOUT)
        if resp.status_code == 404:
            errors.append(f"OSV: CVE {cve_id} not found (404)")
            return affected, aliases, go_ids, errors
        if resp.status_code != 200:
            errors.append(f"OSV: HTTP {resp.status_code}")
            return affected, aliases, go_ids, errors

        data = resp.json()
        aliases = data.get("aliases", [])
        go_ids = [a for a in aliases if a.startswith("GO-")]

        for entry in data.get("affected", []):
            pkg = entry.get("package", {})
            ecosystem = pkg.get("ecosystem", "")
            name = pkg.get("name", "")

            for rng in entry.get("ranges", []):
                version_info = {}
                for evt in rng.get("events", []):
                    if "introduced" in evt:
                        version_info["introduced"] = evt["introduced"]
                    if "fixed" in evt:
                        version_info["fixed"] = evt["fixed"]

                affected.append({
                    "ecosystem": ecosystem,
                    "package": name,
                    "versions": version_info,
                    "source": "osv",
                })

            if not entry.get("ranges"):
                affected.append({
                    "ecosystem": ecosystem,
                    "package": name,
                    "versions": {},
                    "source": "osv",
                })

    except requests.RequestException as e:
        errors.append(f"OSV: request failed: {e}")
    except (KeyError, ValueError) as e:
        errors.append(f"OSV: parse error: {e}")

    return affected, aliases, go_ids, errors


def fetch_go_vuln(go_id):
    affected = []
    errors = []
    try:
        resp = requests.get(GO_VULN_DB.format(go_id=go_id), timeout=TIMEOUT)
        if resp.status_code != 200:
            errors.append(f"Go vuln DB: HTTP {resp.status_code} for {go_id}")
            return affected, errors

        data = resp.json()
        for module in data.get("modules", []):
            mod_path = module.get("module", "")
            for ver in module.get("versions", []):
                version_info = {}
                if "introduced" in ver:
                    version_info["introduced"] = ver["introduced"]
                if "fixed" in ver:
                    version_info["fixed"] = ver["fixed"]

                affected.append({
                    "ecosystem": "Go",
                    "package": mod_path,
                    "versions": version_info,
                    "source": "go_vuln_db",
                    "go_id": go_id,
                })

            packages = module.get("packages", [])
            if packages and not module.get("versions"):
                for pkg in packages:
                    affected.append({
                        "ecosystem": "Go",
                        "package": pkg.get("package", mod_path),
                        "versions": {},
                        "source": "go_vuln_db",
                        "go_id": go_id,
                    })

    except requests.RequestException as e:
        errors.append(f"Go vuln DB: request failed: {e}")
    except (KeyError, ValueError) as e:
        errors.append(f"Go vuln DB: parse error: {e}")

    return affected, errors


def _guess_ecosystem(mitre_entry):
    product = mitre_entry.get("product", "").lower()
    cpes = mitre_entry.get("cpes", [])
    platforms = mitre_entry.get("platforms", [])

    cpe_str = " ".join(cpes).lower() if cpes else ""
    plat_str = " ".join(platforms).lower() if platforms else ""

    if "golang" in product or "go" in plat_str or "/go/" in cpe_str:
        return "Go"
    if "python" in product or "pypi" in product or "python" in plat_str:
        return "PyPI"
    if "npm" in product or "node" in plat_str:
        return "npm"
    if "rpm" in cpe_str or "redhat" in cpe_str or "rhel" in cpe_str:
        return "rpm"
    return ""


def main():
    parser = argparse.ArgumentParser(description="Fetch CVE metadata from multiple sources")
    parser.add_argument("cve_id", help="CVE identifier (e.g., CVE-2024-45490)")
    args = parser.parse_args()

    cve_id = args.cve_id.upper()
    if not re.match(r"^CVE-\d{4}-\d+$", cve_id):
        json.dump({"cve_id": args.cve_id, "error": "Invalid CVE ID format"}, sys.stdout, indent=2)
        sys.exit(1)

    all_affected = []
    all_errors = []

    mitre_affected, description, mitre_errors = fetch_mitre(cve_id)
    all_affected.extend(mitre_affected)
    all_errors.extend(mitre_errors)

    osv_affected, aliases, go_ids, osv_errors = fetch_osv(cve_id)
    all_affected.extend(osv_affected)
    all_errors.extend(osv_errors)

    for go_id in go_ids:
        go_affected, go_errors = fetch_go_vuln(go_id)
        all_affected.extend(go_affected)
        all_errors.extend(go_errors)

    result = {
        "cve_id": cve_id,
        "description": description,
        "affected": all_affected,
        "aliases": aliases,
        "errors": all_errors,
    }

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
