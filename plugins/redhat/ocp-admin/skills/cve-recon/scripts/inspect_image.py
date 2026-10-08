#!/usr/bin/env python3
"""Extract image metadata (labels, creation date, architecture) via regctl."""

import argparse
import json
import shutil
import subprocess
import sys


def run_cmd(cmd, timeout=30):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "command timed out"
    except FileNotFoundError:
        return -1, "", f"command not found: {cmd[0]}"


def get_image_config(image_ref):
    rc, stdout, stderr = run_cmd(["regctl", "image", "config", image_ref])
    if rc != 0:
        return None, f"regctl image config failed: {stderr.strip()}"
    try:
        return json.loads(stdout), None
    except json.JSONDecodeError as e:
        return None, f"regctl output is not valid JSON: {e}"


def get_image_digest(image_ref):
    rc, stdout, stderr = run_cmd(["regctl", "manifest", "digest", image_ref])
    if rc != 0:
        return "", f"regctl manifest digest failed: {stderr.strip()}"
    return stdout.strip(), None


LABEL_KEYS = [
    "cpe",
    "name",
    "com.redhat.component",
    "vendor",
    "maintainer",
    "org.opencontainers.image.created",
    "org.opencontainers.image.title",
    "org.opencontainers.image.description",
    "org.opencontainers.image.vendor",
    "io.k8s.display-name",
    "url",
    "version",
    "release",
]


def main():
    parser = argparse.ArgumentParser(description="Extract image metadata via regctl")
    parser.add_argument("image_ref", help="Container image reference")
    args = parser.parse_args()

    if not shutil.which("regctl"):
        json.dump({
            "image_ref": args.image_ref,
            "error": "regctl not found in PATH",
            "errors": ["regctl not installed"],
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    errors = []

    config, err = get_image_config(args.image_ref)
    if err:
        errors.append(err)

    digest, err = get_image_digest(args.image_ref)
    if err:
        errors.append(err)

    if not config:
        json.dump({
            "image_ref": args.image_ref,
            "digest": digest,
            "labels": {},
            "architecture": "",
            "errors": errors,
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    all_labels = config.get("config", {}).get("Labels", {}) or {}
    labels = {}
    for key in LABEL_KEYS:
        if key in all_labels:
            labels[key] = all_labels[key]

    architecture = config.get("architecture", "")

    result = {
        "image_ref": args.image_ref,
        "digest": digest,
        "labels": labels,
        "architecture": architecture,
        "errors": errors,
    }

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
