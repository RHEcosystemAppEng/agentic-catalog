#!/usr/bin/env python3
"""Download SBOM from a container image via cosign. Returns the full raw SPDX JSON.

Handles image index detection: if the SBOM is for a multi-arch image index,
automatically extracts the linux/amd64 digest and re-fetches the
architecture-specific SBOM.

The output is a JSON envelope with metadata (sbom_source, image_ref, errors)
and the complete raw SPDX document in the 'spdx' field. The LLM should read
and interpret the full SPDX data — packages, relationships, PURLs, versions.
"""

import argparse
import base64
import json
import re
import shutil
import subprocess
import sys


def run_cmd(cmd, timeout=120):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "command timed out"
    except FileNotFoundError:
        return -1, "", f"command not found: {cmd[0]}"


def try_attestation_sbom(image_ref):
    rc, stdout, stderr = run_cmd([
        "cosign", "download", "attestation",
        "--predicate-type=spdx", image_ref
    ])
    if rc != 0:
        return None, f"attestation: {stderr.strip()}"

    for line in stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            envelope = json.loads(line)
            payload = base64.b64decode(envelope.get("payload", ""))
            att = json.loads(payload)
            predicate = att.get("predicate", att)
            if "spdxVersion" in predicate or "packages" in predicate:
                return predicate, None
        except (json.JSONDecodeError, KeyError, Exception):
            continue

    return None, "attestation: no valid SPDX predicate found"


def try_buildtime_sbom(image_ref, platform="linux/amd64"):
    rc, stdout, stderr = run_cmd([
        "cosign", "download", "sbom",
        "--platform", platform, image_ref
    ])
    if rc != 0:
        return None, f"build-time: {stderr.strip()}"

    try:
        sbom = json.loads(stdout)
        if "spdxVersion" in sbom or "packages" in sbom:
            return sbom, None
    except json.JSONDecodeError:
        pass

    return None, "build-time: no valid SPDX JSON found"


def is_image_index_sbom(sbom):
    packages = sbom.get("packages", [])
    return bool(packages and packages[0].get("SPDXID") == "SPDXRef-image-index")


def extract_amd64_digest(sbom):
    for pkg in sbom.get("packages", []):
        for ref in pkg.get("externalRefs", []):
            locator = ref.get("referenceLocator", "")
            if "arch=amd64" in locator or "arch=x86_64" in locator:
                match = re.search(r"@sha256:([a-f0-9]{64})", locator)
                if match:
                    return f"sha256:{match.group(1)}"

        for checksum in pkg.get("checksums", []):
            if checksum.get("algorithm", "").upper() == "SHA256":
                return f"sha256:{checksum['checksumValue']}"

    for rel in sbom.get("relationships", []):
        if rel.get("relationshipType") == "VARIANT_OF":
            element = rel.get("relatedSpdxElement", "")
            match = re.search(r"sha256-([a-f0-9]{64})", element)
            if match:
                return f"sha256:{match.group(1)}"

    return None


def main():
    parser = argparse.ArgumentParser(description="Download SBOM from a container image")
    parser.add_argument("image_ref", help="Container image reference")
    parser.add_argument("--platform", default="linux/amd64", help="Platform (default: linux/amd64)")
    args = parser.parse_args()

    if not shutil.which("cosign"):
        json.dump({"error": "cosign not found in PATH"}, sys.stdout, indent=2)
        sys.exit(1)

    errors = []
    sbom = None
    sbom_source = ""

    sbom, err = try_attestation_sbom(args.image_ref)
    if sbom:
        sbom_source = "attestation"
    else:
        if err:
            errors.append(err)
        sbom, err = try_buildtime_sbom(args.image_ref, args.platform)
        if sbom:
            sbom_source = "build_time"
        else:
            if err:
                errors.append(err)

    if sbom and is_image_index_sbom(sbom):
        digest = extract_amd64_digest(sbom)
        if digest:
            registry_path = args.image_ref.split(":")[0].split("@")[0]
            arch_ref = f"{registry_path}@{digest}"
            errors.append(f"image index detected, re-fetched with {arch_ref}")

            sbom2, err2 = try_attestation_sbom(arch_ref)
            if sbom2:
                sbom = sbom2
                sbom_source = "attestation"
            else:
                sbom2, err2 = try_buildtime_sbom(arch_ref, args.platform)
                if sbom2:
                    sbom = sbom2
                    sbom_source = "build_time"
                else:
                    if err2:
                        errors.append(err2)
        else:
            errors.append("image index detected but could not extract amd64 digest")

    if not sbom:
        json.dump({
            "image_ref": args.image_ref,
            "sbom_source": "",
            "spdx": None,
            "errors": errors if errors else ["no SBOM found"],
        }, sys.stdout, indent=2)
        print()
        sys.exit(0)

    result = {
        "image_ref": args.image_ref,
        "sbom_source": sbom_source,
        "spdx": sbom,
        "errors": errors,
    }

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
