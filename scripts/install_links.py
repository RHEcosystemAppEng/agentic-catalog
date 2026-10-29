#!/usr/bin/env python3
"""Build per-plugin install metadata (git tree, Lola, Claude Code marketplace)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import plugin_registry

CLAUDE_MARKETPLACE_REL = ".claude-plugin/marketplace.json"
CODEX_MARKETPLACE_REL = ".agents/plugins/marketplace.json"
CURSOR_MARKETPLACE_REL = ".cursor-plugin/marketplace.json"
LOLA_MARKETPLACE_REL = "marketplace/rh-agentic-collection.yml"
DEFAULT_HUB_MARKETPLACE_NAME = "ecosystem-plugins"
DEFAULT_CLAUDE_INSTALL_SCOPE = "project"


def _load_marketplace_json(
    rel_path: str, repo_root: Optional[Path] = None
) -> Dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parent.parent
    path = root / rel_path
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _index_plugins_by_name(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    plugins = data.get("plugins") or []
    out: Dict[str, Dict[str, Any]] = {}
    for plugin in plugins:
        if isinstance(plugin, dict) and plugin.get("name"):
            out[str(plugin["name"])] = plugin
    return out


def load_claude_plugins(
    repo_root: Optional[Path] = None,
) -> Dict[str, Dict[str, Any]]:
    data = _load_marketplace_json(str(plugin_registry.DEFAULT_CLAUDE_MARKETPLACE), repo_root)
    return _index_plugins_by_name(data)


def load_codex_plugins(
    repo_root: Optional[Path] = None,
) -> Dict[str, Dict[str, Any]]:
    data = _load_marketplace_json(CODEX_MARKETPLACE_REL, repo_root)
    return _index_plugins_by_name(data)


def load_codex_marketplace_name(repo_root: Optional[Path] = None) -> str:
    data = _load_marketplace_json(CODEX_MARKETPLACE_REL, repo_root)
    return str(data.get("name") or "").strip() or DEFAULT_HUB_MARKETPLACE_NAME


def load_claude_marketplace_name(repo_root: Optional[Path] = None) -> str:
    data = _load_marketplace_json(
        str(plugin_registry.DEFAULT_CLAUDE_MARKETPLACE), repo_root
    )
    return str(data.get("name") or "").strip() or DEFAULT_HUB_MARKETPLACE_NAME


def _repo_clone_dir(repository: str) -> str:
    slug = plugin_registry.web_repo_url(repository)
    return slug.rsplit("/", 1)[-1] if slug else "agentic-catalog"


def load_cursor_plugins(
    repo_root: Optional[Path] = None,
) -> Dict[str, Dict[str, Any]]:
    data = _load_marketplace_json(CURSOR_MARKETPLACE_REL, repo_root)
    return _index_plugins_by_name(data)


def build_install(
    module: Dict[str, Any],
    claude_plugins: Optional[Dict[str, Dict[str, Any]]] = None,
    catalog_branch: Optional[str] = None,
    codex_plugins: Optional[Dict[str, Dict[str, Any]]] = None,
    cursor_plugins: Optional[Dict[str, Dict[str, Any]]] = None,
    codex_marketplace_name: Optional[str] = None,
    claude_marketplace_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Return the ``install`` object stored on each plugin in data.json."""
    name = str(module.get("name") or "")
    repository = str(module.get("repository") or "")
    hub_path = str(module.get("path") or "").strip().strip("/")
    ref = str(module.get("ref") or "").strip() or plugin_registry.catalog_branch()
    branch = catalog_branch or plugin_registry.catalog_branch()

    hub_url = plugin_registry.github_tree_url(repository, ref, hub_path)
    lola_raw = plugin_registry.github_raw_url(repository, branch, LOLA_MARKETPLACE_REL)
    claude_raw = plugin_registry.github_raw_url(
        repository, branch, CLAUDE_MARKETPLACE_REL
    )
    codex_raw = plugin_registry.github_raw_url(repository, branch, CODEX_MARKETPLACE_REL)
    cursor_raw = plugin_registry.github_raw_url(repository, branch, CURSOR_MARKETPLACE_REL)

    claude_entry = (claude_plugins or {}).get(name) or {}
    codex_entry = (codex_plugins or {}).get(name) or {}
    cursor_entry = (cursor_plugins or {}).get(name) or {}
    codex_name = (codex_marketplace_name or "").strip() or DEFAULT_HUB_MARKETPLACE_NAME
    claude_name = (claude_marketplace_name or "").strip() or DEFAULT_HUB_MARKETPLACE_NAME
    codex_source_path = str(
        (codex_entry.get("source") or {}).get("path") or hub_path
    ).lstrip("./")
    repo_git_url = repository.strip() or plugin_registry.web_repo_url(repository)
    clone_dir = _repo_clone_dir(repository)
    scope = DEFAULT_CLAUDE_INSTALL_SCOPE

    install: Dict[str, Any] = {
        "hub_url": hub_url,
        "lola": {
            "marketplace_raw_url": lola_raw,
            "market_alias": plugin_registry.LOLA_MARKET_ALIAS,
            "plugin_name": name,
            "command": (
                f"lola market add {plugin_registry.LOLA_MARKET_ALIAS} {lola_raw}\n"
                f"lola install -f {name}"
            ),
        },
        "claude": {
            "marketplace_json_url": claude_raw,
            "plugin_name": name,
            "marketplace_name": claude_name,
            "source_path": (claude_entry.get("source") or {}).get("path") or hub_path,
            "command": (
                f"claude plugin marketplace add {repo_git_url} --scope {scope}\n"
                f"claude plugin install {name}@{claude_name} --scope {scope}"
            ),
        },
        "codex": {
            "marketplace_json_url": codex_raw,
            "plugin_name": name,
            "marketplace_name": codex_name,
            "source_path": codex_source_path,
            "command": (
                f"codex plugin marketplace add {repo_git_url} --ref {branch}\n"
                f"codex plugin add {name}@{codex_name}"
            ),
        },
        "cursor": {
            "marketplace_json_url": cursor_raw,
            "plugin_name": name,
            "source_path": str(cursor_entry.get("source") or hub_path),
            "command": (
                f"git clone {repo_git_url}\n"
                f"cd {clone_dir} && git checkout {branch}\n"
                "# In Cursor: add this repo root as a plugin marketplace\n"
                "# (reads .cursor-plugin/marketplace.json)\n"
                f"# Install plugin: {name}"
            ),
        },
    }
    return install


def attach_install(
    plugin_entry: Dict[str, Any],
    module: Dict[str, Any],
    claude_plugins: Optional[Dict[str, Dict[str, Any]]] = None,
    catalog_branch: Optional[str] = None,
    codex_plugins: Optional[Dict[str, Dict[str, Any]]] = None,
    cursor_plugins: Optional[Dict[str, Dict[str, Any]]] = None,
    codex_marketplace_name: Optional[str] = None,
    claude_marketplace_name: Optional[str] = None,
) -> None:
    plugin_entry["install"] = build_install(
        module,
        claude_plugins,
        catalog_branch,
        codex_plugins,
        cursor_plugins,
        codex_marketplace_name,
        claude_marketplace_name,
    )


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
    codex = {
        "rh-basic": {
            "name": "rh-basic",
            "source": {"path": "./plugins/redhat/rh-basic"},
        }
    }
    cursor = {
        "rh-basic": {
            "name": "rh-basic",
            "source": "plugins/redhat/rh-basic",
        }
    }
    inst = build_install(
        module,
        claude,
        catalog_branch="main",
        codex_plugins=codex,
        cursor_plugins=cursor,
        codex_marketplace_name="ecosystem-plugins",
        claude_marketplace_name="ecosystem-plugins",
    )
    assert "plugins/redhat/rh-basic" in inst["hub_url"]
    assert "/tree/" in inst["hub_url"]
    assert inst["lola"]["plugin_name"] == "rh-basic"
    assert "/main/" in inst["lola"]["marketplace_raw_url"]
    rc = build_install(module, claude, catalog_branch="rc/v1.0.0")
    assert "rc/v1.0.0" in rc["lola"]["marketplace_raw_url"]
    assert inst["claude"]["plugin_name"] == "rh-basic"
    assert inst["claude"]["marketplace_name"] == "ecosystem-plugins"
    assert "claude plugin marketplace add" in inst["claude"]["command"]
    assert "claude plugin install rh-basic@ecosystem-plugins" in inst["claude"]["command"]
    assert ".claude-plugin/marketplace.json" in inst["claude"]["marketplace_json_url"]
    assert ".agents/plugins/marketplace.json" in inst["codex"]["marketplace_json_url"]
    assert inst["codex"]["marketplace_name"] == "ecosystem-plugins"
    assert inst["codex"]["source_path"] == "plugins/redhat/rh-basic"
    assert "codex plugin marketplace add" in inst["codex"]["command"]
    assert "codex plugin add rh-basic@ecosystem-plugins" in inst["codex"]["command"]
    assert ".cursor-plugin/marketplace.json" in inst["cursor"]["marketplace_json_url"]
    assert inst["cursor"]["source_path"] == "plugins/redhat/rh-basic"
    assert "git clone" in inst["cursor"]["command"]
    assert "Install plugin: rh-basic" in inst["cursor"]["command"]
    # Defaults (no codex/cursor marketplace files loaded) still populate paths.
    bare = build_install(module, claude, catalog_branch="main")
    assert bare["codex"]["marketplace_name"] == DEFAULT_HUB_MARKETPLACE_NAME
    assert bare["claude"]["marketplace_name"] == DEFAULT_HUB_MARKETPLACE_NAME
    assert bare["codex"]["source_path"] == "plugins/redhat/rh-basic"
    assert bare["cursor"]["source_path"] == "plugins/redhat/rh-basic"
    print("install_links self-test OK")


if __name__ == "__main__":
    _self_test()
