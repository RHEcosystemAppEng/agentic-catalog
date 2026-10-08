#!/usr/bin/env python3
"""Build per-pack install metadata (git tree, Lola, Claude Code marketplace)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import pack_registry

CLAUDE_MARKETPLACE_REL = "claude-marketplace/marketplace.json"
LOLA_MARKETPLACE_REL = "marketplace/rh-agentic-collection.yml"


def load_claude_plugins(
    repo_root: Optional[Path] = None,
) -> Dict[str, Dict[str, Any]]:
    root = repo_root or Path(__file__).resolve().parent.parent
    path = root / pack_registry.DEFAULT_CLAUDE_MARKETPLACE
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    plugins = data.get("plugins") or []
    out: Dict[str, Dict[str, Any]] = {}
    for plugin in plugins:
        if isinstance(plugin, dict) and plugin.get("name"):
            out[str(plugin["name"])] = plugin
    return out


def build_install(
    module: Dict[str, Any],
    claude_plugins: Optional[Dict[str, Dict[str, Any]]] = None,
    catalog_branch: Optional[str] = None,
) -> Dict[str, Any]:
    """Return the ``install`` object stored on each pack in data.json."""
    name = str(module.get("name") or "")
    repository = str(module.get("repository") or "")
    hub_path = str(module.get("path") or "").strip().strip("/")
    ref = str(module.get("ref") or "").strip() or pack_registry.catalog_branch()
    branch = catalog_branch or pack_registry.catalog_branch()

    hub_url = pack_registry.github_tree_url(repository, ref, hub_path)
    lola_raw = pack_registry.github_raw_url(repository, branch, LOLA_MARKETPLACE_REL)
    claude_raw = pack_registry.github_raw_url(
        repository, branch, CLAUDE_MARKETPLACE_REL
    )

    claude_entry = (claude_plugins or {}).get(name) or {}
    marketplace_name = None
    # marketplace.json top-level name is not on the plugin entry; callers may
    # still want the plugin name for Claude Code install.
    install: Dict[str, Any] = {
        "hub_url": hub_url,
        "lola": {
            "marketplace_raw_url": lola_raw,
            "market_alias": pack_registry.LOLA_MARKET_ALIAS,
            "pack_name": name,
            "command": (
                f"lola market add {pack_registry.LOLA_MARKET_ALIAS} {lola_raw}\n"
                f"lola install -f {name}"
            ),
        },
        "claude": {
            "marketplace_json_url": claude_raw,
            "plugin_name": name,
            "marketplace_name": marketplace_name,
            "source_path": (claude_entry.get("source") or {}).get("path") or hub_path,
        },
    }
    return install


def attach_install(
    pack: Dict[str, Any],
    module: Dict[str, Any],
    claude_plugins: Optional[Dict[str, Dict[str, Any]]] = None,
    catalog_branch: Optional[str] = None,
) -> None:
    pack["install"] = build_install(module, claude_plugins, catalog_branch)


def _self_test() -> None:
    module = {
        "name": "rh-basic",
        "repository": "https://github.com/RHEcosystemAppEng/agentic-catalog.git",
        "path": "plugins/redhat/rh-basic",
        "ref": "feeb8f54fc8e84b18e933aff9a4a25f8ec6e1388",
    }
    claude = {
        "rh-basic": {
            "name": "rh-basic",
            "source": {"path": "plugins/redhat/rh-basic"},
        }
    }
    inst = build_install(module, claude, catalog_branch="main")
    assert "plugins/redhat/rh-basic" in inst["hub_url"]
    assert "/tree/" in inst["hub_url"]
    assert inst["lola"]["pack_name"] == "rh-basic"
    assert "/main/" in inst["lola"]["marketplace_raw_url"]
    rc = build_install(module, claude, catalog_branch="rc/v1.0.0")
    assert "rc/v1.0.0" in rc["lola"]["marketplace_raw_url"]
    assert inst["claude"]["plugin_name"] == "rh-basic"
    assert "claude-marketplace/marketplace.json" in inst["claude"]["marketplace_json_url"]
    print("install_links self-test OK")


if __name__ == "__main__":
    _self_test()
