"""
Resolve the set of agentic pack directories from the Lola marketplace file.

The marketplace file (``marketplace/rh-agentic-collection.yml``) is the single
source of truth for pack discovery.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

DEFAULT_MARKETPLACE = Path("marketplace/rh-agentic-collection.yml")
DEFAULT_CLAUDE_MARKETPLACE = Path("claude-marketplace/marketplace.json")
# Consumer install / Pages branch. Override with CATALOG_BRANCH (e.g. rc/v1.0.0).
DEFAULT_CATALOG_BRANCH = "main"
LOLA_MARKET_ALIAS = "rh-agentic-collections"


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


REPOSITORY_REF_SHA_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


def repository_ref_error(ref: Any) -> Optional[str]:
    """Return an error message when *ref* is set but not a 40-character commit SHA."""
    if ref is None or not str(ref).strip():
        return None  # absent ref → defaults to main branch
    value = str(ref).strip()
    if not REPOSITORY_REF_SHA_RE.fullmatch(value):
        return (
            f"ref must be a 40-character commit SHA, not a branch or tag (got {value!r})"
        )
    return None


def normalize_repository_ref(ref: Any) -> str:
    """Return a lowercase 40-character commit SHA, or 'main' when ref is absent."""
    err = repository_ref_error(ref)
    if err:
        raise ValueError(err)
    value = str(ref).strip() if ref is not None else ""
    return value.lower() if value else "main"


def validate_repository_module_entry(module: Dict[str, Any]) -> List[str]:
    """Return validation errors for a repository marketplace module entry."""
    name = module.get("name") or "<unknown>"
    err = repository_ref_error(module.get("ref"))
    if err:
        return [f"{name}: {err}"]
    return []


def load_repository_modules(
    marketplace_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Return all marketplace modules that have an external repository."""
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
        if isinstance(m, dict) and m.get("repository", "").strip()
    ]


def load_on_disk_modules(
    repo_root: Optional[Path] = None,
    marketplace_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Marketplace modules whose ``path`` exists on this checkout.

    Modules still pointing at authoring layouts (e.g. ``rh-developer``) are
    omitted until they are published onto the hub tree.
    """
    root = repo_root or _repo_root()
    out: List[Dict[str, Any]] = []
    for mod in load_repository_modules(marketplace_path):
        raw = str(mod.get("path") or "").strip().strip("/")
        if not raw or raw == ".":
            continue
        if (root / raw).is_dir():
            out.append(mod)
    return out


def catalog_branch() -> str:
    value = os.environ.get("CATALOG_BRANCH", "").strip()
    return value or DEFAULT_CATALOG_BRANCH


def web_repo_url(repository: str) -> str:
    """HTTPS repo URL without trailing slash or ``.git`` suffix."""
    return str(repository or "").strip().rstrip("/").removesuffix(".git")


def github_blob_base(repository: str, ref: str, subpath: str = "") -> str:
    """Blob URL for a file under *subpath* at *ref* (GitHub or GitLab)."""
    repo = web_repo_url(repository)
    if not repo:
        return ""
    ref_part = (ref or "main").strip() or "main"
    path = str(subpath or "").strip().strip("/")
    blob_sep = "/-/blob" if "gitlab.com" in repo else "/blob"
    base = f"{repo}{blob_sep}/{ref_part}"
    return f"{base}/{path}" if path and path != "." else base


def github_tree_url(repository: str, ref: str, subpath: str = "") -> str:
    """Directory tree URL for a pack at *ref*."""
    repo = web_repo_url(repository)
    if not repo:
        return ""
    ref_part = (ref or "main").strip() or "main"
    path = str(subpath or "").strip().strip("/")
    tree_sep = "/-/tree" if "gitlab.com" in repo else "/tree"
    base = f"{repo}{tree_sep}/{ref_part}"
    return f"{base}/{path}" if path and path != "." else base


def github_raw_url(repository: str, ref: str, rel_path: str) -> str:
    """Raw file URL on GitHub (or GitLab) for a path at *ref*."""
    repo = web_repo_url(repository)
    rel = str(rel_path or "").lstrip("/")
    ref_part = (ref or "main").strip() or "main"
    if "github.com" in repo:
        slug = repo.split("github.com/", 1)[-1]
        return f"https://raw.githubusercontent.com/{slug}/{ref_part}/{rel}"
    if "gitlab.com" in repo:
        return f"{repo}/-/raw/{ref_part}/{rel}"
    return f"{repo}/{rel}"


# Catalog `maturity` value published to GitHub Pages / docs/data.json.
DOCS_MATURITY_PUBLISH: str = "GREEN"
