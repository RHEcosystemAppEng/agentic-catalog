"""
Resolve <pack>/.catalog/collection.yaml for static site embedding (fragment files inlined).

Used by build_website.py only. Does not replace collection.yaml on disk.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

CATALOG_FRAGMENT_FIELD_KEYS = (
    "documentation_section",
    "mcp_section",
    "security_model",
    "deploy_and_use",
)


def _catalog_fragment_rel_path(value: str) -> Optional[str]:
    s = value.strip()
    if "\n" in s or "\r" in s:
        return None
    m = re.fullmatch(r"#\s*(?:\.catalog/)?([\w./-]+\.md)\s*", s, flags=re.IGNORECASE)
    if not m:
        return None
    rel = m.group(1)
    if ".." in rel or rel.startswith("/"):
        return None
    return rel


def _read_yaml_catalog(pack_dir: str, root: Path) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    p = root / pack_dir / ".catalog" / "collection.yaml"
    if not p.exists():
        return None, [f"{pack_dir}: missing {p.relative_to(root)}"]
    try:
        with open(p, "r", encoding="utf-8") as f:
            raw = f.read()
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            return None, [f"{pack_dir}: collection.yaml must parse to a mapping"]
        return data, []
    except Exception as e:
        return None, [f"{pack_dir}: failed to parse collection.yaml: {e}"]


def _strip_leading_catalog_comment(markdown: str) -> str:
    s = markdown.lstrip("﻿")
    if not s.lstrip().startswith("<!--"):
        return markdown
    m = re.match(r"^\s*<!--.*?-->\s*", s, flags=re.DOTALL)
    if not m:
        return markdown
    return s[m.end() :].lstrip("\n")


def _read_fragment(pack_dir: str, ref: str, root: Path) -> Tuple[Optional[str], Optional[str]]:
    rel = _catalog_fragment_rel_path(ref)
    if not rel:
        return None, f"invalid fragment ref {ref!r}"
    catalog_dir = (root / pack_dir / ".catalog").resolve()
    target = (catalog_dir / rel).resolve()
    try:
        target.relative_to(catalog_dir)
    except ValueError:
        return None, f"fragment escapes .catalog: {ref!r}"
    if not target.is_file():
        return None, f"missing fragment {rel}"
    raw = target.read_text(encoding="utf-8")
    return _strip_leading_catalog_comment(raw), None


def bundle_catalog_for_site(pack_dir: str, root: Path) -> Tuple[Optional[Dict[str, Any]], list[str]]:
    """
    Load catalog YAML and inline all #fragment file references for JSON export.

    Returns:
        (dict suitable for docs/data.json, list of warning strings)
    """
    data, errs = _read_yaml_catalog(pack_dir, root)
    if errs or data is None:
        return None, errs
    out: Dict[str, Any] = copy.deepcopy(data)
    warnings: list[str] = []

    for key in CATALOG_FRAGMENT_FIELD_KEYS:
        val = out.get(key)
        if not isinstance(val, str) or not val.strip():
            continue
        if not _catalog_fragment_rel_path(val):
            continue
        text, err = _read_fragment(pack_dir, val, root)
        if err:
            warnings.append(f"{pack_dir}: {key}: {err}")
            continue
        out[key] = text

    return out, warnings
