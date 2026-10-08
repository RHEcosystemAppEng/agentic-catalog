#!/usr/bin/env python3
"""Validate CVE ID, image reference, and batch input file."""

import argparse
import json
import os
import re
import sys

CVE_RE = re.compile(r"^CVE-\d{4}-\d+$", re.IGNORECASE)
RHSA_RE = re.compile(r"^RHSA-\d{4}[:\-]\d+$", re.IGNORECASE)

IMAGE_REF_SAFE_CHARS = re.compile(r"^[a-zA-Z0-9._/:\-@]+$")
IMAGE_REF_STRUCTURE = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9._\-]*(?::\d+)?"
    r"(?:/[a-zA-Z0-9._\-]+)+"
    r"(?::[a-zA-Z0-9._\-]+|@sha256:[a-f0-9]{64})?$"
)

MAX_IMAGE_REF_LEN = 512
MAX_FILE_ROWS = 500
MAX_FILE_BYTES = 1 * 1024 * 1024

OCP_VERSION_RE = re.compile(r"^4\.\d+\.\d+$")

KNOWN_REDHAT_REGISTRIES = [
    "registry.redhat.io",
    "registry.access.redhat.com",
]

KNOWN_REDHAT_PREFIXES = [
    "quay.io/openshift-release-dev/",
    "quay.io/redhat-user-workloads/",
]


def validate_cve_id(cve_id):
    if not cve_id:
        return "CVE ID is empty"
    if not CVE_RE.match(cve_id):
        return f"Invalid CVE ID format: '{cve_id}'. Expected: CVE-YYYY-NNNNN"
    return None


def validate_advisory_id(advisory_id):
    if not advisory_id:
        return "Advisory ID is empty"
    if not RHSA_RE.match(advisory_id):
        return f"Invalid advisory ID format: '{advisory_id}'. Expected: RHSA-YYYY:NNNNN"
    return None


def is_rhsa_id(value):
    return bool(RHSA_RE.match(value)) if value else False


def validate_image_ref(ref):
    if not ref:
        return "image reference is empty"
    if len(ref) > MAX_IMAGE_REF_LEN:
        return f"image reference exceeds maximum length of {MAX_IMAGE_REF_LEN} characters"
    if not IMAGE_REF_SAFE_CHARS.match(ref):
        bad = sorted({c for c in ref if not re.match(r"[a-zA-Z0-9._/:\-@]", c)})
        return f"image reference contains disallowed characters: {bad}"
    if "/" not in ref:
        return "image reference must include a registry hostname (no '/' found)"
    if not IMAGE_REF_STRUCTURE.match(ref):
        return "image reference does not match expected format: registry/namespace/image[:tag|@sha256:digest]"
    return None


def classify_registry(image_ref):
    registry = image_ref.split("/")[0]

    if registry in KNOWN_REDHAT_REGISTRIES:
        return {"registry": registry, "is_redhat": True, "type": "official"}

    for prefix in KNOWN_REDHAT_PREFIXES:
        if image_ref.startswith(prefix):
            return {"registry": registry, "is_redhat": True, "type": "mirror", "prefix": prefix}

    return {"registry": registry, "is_redhat": False, "type": "unknown"}


def classify_ref_format(image_ref):
    if "@sha256:" in image_ref:
        return "digest"
    if ":" in image_ref.split("/")[-1]:
        return "tag"
    return "untagged"


def validate_batch_file(path):
    errors = []
    entries = []

    if not os.path.isfile(path):
        return entries, [f"Input file not found: {path}"]

    file_size = os.path.getsize(path)
    if file_size > MAX_FILE_BYTES:
        return entries, [f"Input file too large ({file_size} bytes, max {MAX_FILE_BYTES})"]

    try:
        with open(path, "r") as f:
            lines = f.readlines()
    except OSError as e:
        return entries, [f"Cannot read input file: {e}"]

    data_row_count = 0
    header_skipped = False

    for line_num, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if not line:
            continue
        if line.startswith("#"):
            continue

        if not header_skipped and "cve_id" in line.lower().split(",")[0]:
            header_skipped = True
            continue

        parts = line.split(",")
        if len(parts) != 2:
            errors.append(f"Line {line_num}: expected 2 comma-separated values, got {len(parts)}")
            continue

        cve_id = parts[0].strip()
        image_ref = parts[1].strip()

        cve_err = validate_cve_id(cve_id)
        if cve_err:
            errors.append(f"Line {line_num}: {cve_err}")

        img_err = validate_image_ref(image_ref)
        if img_err:
            errors.append(f"Line {line_num}: {img_err}")

        data_row_count += 1
        if data_row_count > MAX_FILE_ROWS:
            errors.append(f"Line {line_num}: exceeds maximum of {MAX_FILE_ROWS} data rows")
            break

        if not cve_err and not img_err:
            registry_info = classify_registry(image_ref)
            entries.append({
                "cve_id": cve_id.upper(),
                "image_ref": image_ref,
                "ref_format": classify_ref_format(image_ref),
                "registry": registry_info,
            })

    return entries, errors


def validate_ocp_version(version):
    if not version:
        return "OCP version is empty"
    if not OCP_VERSION_RE.match(version):
        return f"Invalid OCP version format: '{version}'. Expected: 4.X.Y (e.g., 4.20.17)"
    return None


def main():
    parser = argparse.ArgumentParser(description="Validate CVE and image input")
    parser.add_argument("--cve", default="", help="CVE identifier or RHSA advisory ID")
    parser.add_argument("--image", default="", help="Container image reference")
    parser.add_argument("--file", default="", help="Path to CSV batch input file")
    parser.add_argument("--coreos", action="store_true", help="CoreOS validation mode")
    parser.add_argument("--ocp-version", default="", help="OCP version for CoreOS mode (e.g., 4.20.17)")
    args = parser.parse_args()

    if args.coreos:
        errors = []

        input_type = "cve"
        if is_rhsa_id(args.cve):
            input_type = "rhsa"
            adv_err = validate_advisory_id(args.cve)
            if adv_err:
                errors.append(adv_err)
        else:
            cve_err = validate_cve_id(args.cve)
            if cve_err:
                errors.append(cve_err)

        ocp_err = validate_ocp_version(args.ocp_version)
        if ocp_err:
            errors.append(ocp_err)

        entries = []
        if not errors:
            entry = {"ocp_version": args.ocp_version, "input_type": input_type}
            if input_type == "rhsa":
                entry["advisory_id"] = args.cve.upper()
            else:
                entry["cve_id"] = args.cve.upper()
            entries.append(entry)

        result = {
            "valid": len(errors) == 0,
            "mode": "coreos",
            "entries": entries,
            "errors": errors,
        }
    elif args.file:
        entries, errors = validate_batch_file(args.file)
        result = {
            "valid": len(errors) == 0 and len(entries) > 0,
            "mode": "batch",
            "file": args.file,
            "entry_count": len(entries),
            "entries": entries,
            "errors": errors,
        }
    elif args.cve or args.image:
        errors = []

        input_type = "cve"
        if is_rhsa_id(args.cve):
            input_type = "rhsa"
            adv_err = validate_advisory_id(args.cve)
            if adv_err:
                errors.append(adv_err)
        else:
            cve_err = validate_cve_id(args.cve)
            if cve_err:
                errors.append(cve_err)

        img_err = validate_image_ref(args.image)
        if img_err:
            errors.append(img_err)

        registry_info = classify_registry(args.image) if not img_err else {}

        entries = []
        if not errors:
            entry = {
                "image_ref": args.image,
                "ref_format": classify_ref_format(args.image),
                "registry": registry_info,
                "input_type": input_type,
            }
            if input_type == "rhsa":
                entry["advisory_id"] = args.cve.upper()
            else:
                entry["cve_id"] = args.cve.upper()
            entries.append(entry)

        result = {
            "valid": len(errors) == 0,
            "mode": "single",
            "entries": entries,
            "errors": errors,
        }
    else:
        result = {
            "valid": False,
            "mode": "",
            "entries": [],
            "errors": ["No input provided. Use --cve and --image, --file for batch, or --coreos with --ocp-version."],
        }

    json.dump(result, sys.stdout, indent=2)
    print()
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
