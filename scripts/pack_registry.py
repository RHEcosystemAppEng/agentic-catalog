"""
Resolve the set of agentic pack directories from the Lola marketplace file.

The marketplace file (``marketplace/rh-agentic-collection.yml``) is the single
source of truth for pack discovery.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

DEFAULT_MARKETPLACE = Path("marketplace/rh-agentic-collection.yml")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_marketplace_module_paths(marketplace_path: Optional[Path] = None) -> List[str]:
    path = marketplace_path or (_repo_root() / DEFAULT_MARKETPLACE)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    modules = data.get("modules") or []
    out: List[str] = []
    for mod in modules:
        p = mod.get("path")
        if isinstance(p, str) and p.strip():
            out.append(p.strip().strip("/"))
    return out


def get_union_pack_dirs(
    repo_root: Optional[Path] = None,
    marketplace_path: Optional[Path] = None,
) -> List[str]:
    """
    Sorted pack directory names from the marketplace that exist on disk under repo root.
    The marketplace file is the single source of truth for pack discovery.
    """
    root = repo_root or _repo_root()
    names: Set[str] = set(load_marketplace_module_paths(marketplace_path))
    return [name for name in sorted(names) if (root / name).is_dir()]


def load_marketplace_module_by_path(
    pack_dir: str,
    repo_root: Optional[Path] = None,
    marketplace_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Return the marketplace module dict for a pack path, or None."""
    root = repo_root or _repo_root()
    path = marketplace_path or (root / DEFAULT_MARKETPLACE)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    for mod in data.get("modules") or []:
        if mod.get("path") == pack_dir:
            return mod
    return None


MAIN_REPO_URL = "https://github.com/RHEcosystemAppEng/agentic-collections"

FEDERATION_REF_SHA_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


def federation_ref_error(ref: Any) -> Optional[str]:
    """Return an error message when *ref* is set but not a 40-character commit SHA."""
    if ref is None or not str(ref).strip():
        return None  # absent ref → defaults to main branch
    value = str(ref).strip()
    if not FEDERATION_REF_SHA_RE.fullmatch(value):
        return (
            f"ref must be a 40-character commit SHA, not a branch or tag (got {value!r})"
        )
    return None


def normalize_federation_ref(ref: Any) -> str:
    """Return a lowercase 40-character commit SHA, or 'main' when ref is absent."""
    err = federation_ref_error(ref)
    if err:
        raise ValueError(err)
    value = str(ref).strip() if ref is not None else ""
    return value.lower() if value else "main"


def validate_federated_module_entry(module: Dict[str, Any]) -> List[str]:
    """Return validation errors for a federated marketplace module entry."""
    name = module.get("name") or "<unknown>"
    err = federation_ref_error(module.get("ref"))
    if err:
        return [f"{name}: {err}"]
    return []


def load_federated_modules(
    marketplace_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Return modules whose repository differs from the main repo (federated packs)."""
    path = marketplace_path or (_repo_root() / DEFAULT_MARKETPLACE)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    modules = data.get("modules") or []
    if not isinstance(modules, list):
        return []
    return [
        m for m in modules
        if isinstance(m, dict)
        and m.get("repository", "").rstrip("/") != MAIN_REPO_URL
    ]


# Catalog `maturity` value published to GitHub Pages / docs/data.json.
DOCS_MATURITY_PUBLISH: str = "GREEN"
