#!/usr/bin/env python3
"""Scan a container image repository for images built after a given date.

Lists image tags with their build dates, digests, and CPEs. Used to find
newer images that may contain a patched RPM.
"""

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


def list_tags(repo):
    rc, stdout, stderr = run_cmd(["regctl", "tag", "ls", repo], timeout=60)
    if rc != 0:
        return [], f"regctl tag ls failed: {stderr.strip()}"
    tags = []
    for line in stdout.strip().split("\n"):
        tag = line.strip()
        if not tag:
            continue
        if tag.startswith("sha") or tag == "source" or tag == "latest":
            continue
        tags.append(tag)
    return tags, None


def inspect_tag(repo, tag):
    ref = f"{repo}:{tag}"

    rc, stdout, stderr = run_cmd(
        ["regctl", "image", "config", ref, "--format",
         "{{.Created}}|{{index .Config.Labels \"cpe\"}}|{{.Digest}}"],
        timeout=15
    )
    if rc != 0:
        return None

    parts = stdout.strip().split("|")
    if len(parts) < 3:
        return None

    return {
        "tag": tag,
        "created": parts[0],
        "cpe": parts[1] if len(parts) > 1 else "",
        "digest": parts[2] if len(parts) > 2 else "",
    }


def main():
    parser = argparse.ArgumentParser(description="Scan repository for newer images")
    parser.add_argument("repo", help="Image repository (e.g., registry.redhat.io/ubi9/ubi)")
    parser.add_argument("--since", required=True, help="ISO 8601 date — only show images built after this")
    parser.add_argument("--max-results", type=int, default=10, help="Max results (default 10)")
    parser.add_argument("--parallel", type=int, default=15, help="Parallel checks (default 15)")
    args = parser.parse_args()

    if not shutil.which("regctl"):
        json.dump({
            "repo": args.repo,
            "error": "regctl not found in PATH",
            "newer_images": [],
            "errors": ["regctl not installed"],
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    tags, err = list_tags(args.repo)
    if err:
        json.dump({
            "repo": args.repo,
            "since": args.since,
            "newer_images": [],
            "errors": [err],
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    if not tags:
        json.dump({
            "repo": args.repo,
            "since": args.since,
            "newer_images": [],
            "total_tags": 0,
            "errors": [],
        }, sys.stdout, indent=2)
        print()
        sys.exit(0)

    # Check tags in batches using subprocess parallelism
    import concurrent.futures

    newer = []
    errors = []

    def check_tag(tag):
        return inspect_tag(args.repo, tag)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {executor.submit(check_tag, tag): tag for tag in tags}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result and result["created"] > args.since:
                newer.append(result)

    # Sort by created date descending, deduplicate by digest
    newer.sort(key=lambda x: x["created"], reverse=True)
    seen_digests = set()
    deduped = []
    for img in newer:
        if img["digest"] not in seen_digests:
            seen_digests.add(img["digest"])
            deduped.append(img)
        if len(deduped) >= args.max_results:
            break

    result = {
        "repo": args.repo,
        "since": args.since,
        "total_tags_checked": len(tags),
        "newer_images": deduped,
        "count": len(deduped),
        "errors": errors,
    }

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
