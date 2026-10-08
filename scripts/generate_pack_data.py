#!/usr/bin/env python3
"""
Parse hub pack trees and extract plugin metadata and skills.

Reads this checkout only (marketplace YAML + plugins/redhat/*). Does not clone.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

import pack_registry
from generate_mcp_data import parse_mcp_file
from install_links import attach_install, load_claude_plugins
from marketplace_eval_enrichment import apply_marketplace_eval


def parse_yaml_frontmatter(file_path: Path) -> Dict[str, Any]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return {}
        import yaml
        return yaml.safe_load(match.group(1)) or {}
    except Exception as e:
        print(f"Warning: Failed to parse frontmatter from {file_path}: {e}")
        return {}


def parse_skills(pack_dir: str) -> List[Dict[str, Any]]:
    """
    Parse skills from skills/*/SKILL.md (multi-skill pack) or SKILL.md at root (single-skill repo).
    """
    skills = []
    root = Path(pack_dir)

    root_skill = root / 'SKILL.md'
    if root_skill.is_file():
        frontmatter = parse_yaml_frontmatter(root_skill)
        name = frontmatter.get('name', root.name)
        description = frontmatter.get('description', '')
        if isinstance(description, str):
            description = ' '.join(description.split())
        return [{'name': name, 'description': description, 'file_path': 'SKILL.md'}]

    skills_dir = root / 'skills'
    if not skills_dir.exists():
        return skills

    for skill_file in skills_dir.glob('*/SKILL.md'):
        frontmatter = parse_yaml_frontmatter(skill_file)

        name = frontmatter.get('name', skill_file.parent.name)
        description = frontmatter.get('description', '')

        if isinstance(description, str):
            description = ' '.join(description.split())

        skills.append({
            'name': name,
            'description': description,
            'file_path': str(skill_file.relative_to(pack_dir))
        })

    return sorted(skills, key=lambda s: s['name'])


def detect_repo_license(repo_root: Path, pack_path: str = ".") -> str:
    """Best-effort SPDX identifier from LICENSE files in this checkout."""
    candidates = [
        repo_root / pack_path / "LICENSE",
        repo_root / pack_path / "LICENSE.txt",
        repo_root / "LICENSE",
        repo_root / "LICENSE.txt",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")[:8000]
        except OSError:
            continue
        upper = text.upper()
        if "APACHE LICENSE" in upper and "VERSION 2.0" in upper:
            return "Apache-2.0"
        if "MIT LICENSE" in upper or "PERMISSION IS HEREBY GRANTED, FREE OF CHARGE" in upper:
            return "MIT"
        if "BSD 3-CLAUSE" in upper or "REDISTRIBUTION AND USE IN SOURCE AND BINARY FORMS" in upper:
            if "3-CLAUSE" in upper or "3 CLAUSE" in upper:
                return "BSD-3-Clause"
            return "BSD-2-Clause"
    return "Unknown"


def load_plugin_json(pack_dir: Path) -> Dict[str, Any]:
    path = pack_dir / "plugin.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Warning: failed to parse {path}: {exc}")
        return {}


def _display_ref(module: Dict[str, Any]) -> str:
    raw = module.get("ref")
    err = pack_registry.repository_ref_error(raw)
    if err or not raw:
        return pack_registry.normalize_repository_ref(raw) if not err else "main"
    return pack_registry.normalize_repository_ref(raw)


def load_hub_packs() -> List[Dict[str, Any]]:
    """Load packs whose marketplace path exists on this checkout."""
    repo_root = Path(__file__).resolve().parent.parent
    modules = pack_registry.load_repository_modules()
    if not modules:
        return []

    on_disk_paths = set(pack_registry.get_union_pack_dirs(repo_root))
    claude_plugins = load_claude_plugins(repo_root)
    packs: List[Dict[str, Any]] = []

    for mod in modules:
        name = mod.get("name", "unknown")
        repository = str(mod.get("repository") or "").strip()
        pack_path = str(mod.get("path") or "").strip().strip("/")
        description = mod.get("description", "")
        version = mod.get("version", "0.0.0")
        tags = mod.get("tags", [])

        if not pack_path:
            print(f"  Warning: marketplace module '{name}' missing path, skipping")
            continue
        if pack_path not in on_disk_paths:
            print(f"  Skipping '{name}': path {pack_path!r} is not on this checkout")
            continue

        pack_dir = repo_root / pack_path
        plugin_json = load_plugin_json(pack_dir)
        license_id = plugin_json.get("license") or detect_repo_license(repo_root, pack_path)
        skills = parse_skills(str(pack_dir))

        readme_path = pack_dir / "README.md"
        readme_content = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else None

        mcp_servers = parse_mcp_file(str(pack_dir))
        for s in mcp_servers:
            s["pack"] = name

        author = plugin_json.get("author")
        if not isinstance(author, dict):
            author = {"name": "Red Hat"}
        elif not author.get("name"):
            author = {**author, "name": "Red Hat"}

        ref = _display_ref(mod)
        pack = {
            "name": name,
            "path": pack_path,
            "hub_path": pack_path,
            "repository": repository,
            "ref": ref,
            "icon": mod.get("icon", ""),
            "plugin": {
                "name": plugin_json.get("name") or name,
                "title": mod.get("title") or name.replace("-", " ").title(),
                "version": plugin_json.get("version") or version,
                "description": description,
                "author": author,
                "license": license_id,
                "keywords": tags,
            },
            "skills": sorted(skills, key=lambda s: s["name"]),
            "agents": [],
            "docs": [],
            "has_readme": readme_content is not None,
            "readme_content": readme_content,
            "mcp_servers_raw": mcp_servers,
        }
        apply_marketplace_eval(pack, mod)
        attach_install(pack, mod, claude_plugins)
        packs.append(pack)
        mcp_status = f", {len(mcp_servers)} MCP server(s)" if mcp_servers else ""
        print(f"  ✓ '{name}': {len(skills)} skill(s) from {pack_path} (README + mcp.json{mcp_status})")

    return packs


def generate_pack_data() -> List[Dict[str, Any]]:
    """
    Generate pack data for all hub packs present on this checkout.

    Returns:
        List of pack dictionaries
    """
    packs = load_hub_packs()
    if packs:
        print(f"✓ Added {len(packs)} marketplace pack(s) from this checkout")
    return packs


if __name__ == '__main__':
    print("Parsing agentic collections...")
    print()

    packs = generate_pack_data()

    print()
    print(f"Found {len(packs)} collections total")
    print()
    print("Summary:")
    for pack in packs:
        plugin = pack['plugin']
        title = plugin.get('title', plugin['name'])
        print(f"  • {title} v{plugin['version']}")
        print(f"    ({plugin['name']})")
        print(f"    Skills: {len(pack['skills'])}, Agents: {len(pack['agents'])}, Docs: {len(pack['docs'])}")
