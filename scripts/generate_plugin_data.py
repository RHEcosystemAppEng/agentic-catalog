#!/usr/bin/env python3
"""
Parse agentic plugins and extract plugin metadata, skills, and agents.
"""

import re
from pathlib import Path
from typing import Dict, List, Any
import yaml

import plugin_registry
from catalog_site_bundle import bundle_catalog_for_site
from eval_site_enrichment import apply_eval_enrichment
from generate_mcp_data import parse_mcp_file

def parse_yaml_frontmatter(file_path: Path) -> Dict[str, Any]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return {}
        return yaml.safe_load(match.group(1)) or {}
    except Exception as e:
        print(f"Warning: Failed to parse frontmatter from {file_path}: {e}")
        return {}


def parse_skills(plugin_dir: str) -> List[Dict[str, Any]]:
    """
    Parse skills from skills/*/SKILL.md (multi-skill plugin) or SKILL.md at root (single-skill repo).
    """
    skills = []
    root = Path(plugin_dir)

    # Single-skill repo: SKILL.md at the plugin root
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

    # Find all SKILL.md files
    for skill_file in skills_dir.glob('*/SKILL.md'):
        frontmatter = parse_yaml_frontmatter(skill_file)

        # Extract name and description
        name = frontmatter.get('name', skill_file.parent.name)
        description = frontmatter.get('description', '')

        # Clean up description (remove leading/trailing whitespace, collapse newlines)
        if isinstance(description, str):
            description = ' '.join(description.split())

        skills.append({
            'name': name,
            'description': description,
            'file_path': str(skill_file.relative_to(plugin_dir))
        })

    return sorted(skills, key=lambda s: s['name'])


def detect_repo_license(repo_root: Path, plugin_path: str = ".") -> str:
    """Best-effort SPDX identifier from LICENSE files in a cloned repository."""
    candidates = [
        repo_root / plugin_path / "LICENSE",
        repo_root / plugin_path / "LICENSE.txt",
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


def load_repository_plugins() -> List[Dict[str, Any]]:
    """Clone each marketplace module and return it as a standalone plugin entry."""
    import shutil
    import subprocess
    import tempfile

    modules = plugin_registry.load_repository_modules()
    if not modules:
        return []

    repo_root = Path(__file__).resolve().parent.parent
    plugins: List[Dict[str, Any]] = []
    tmp = Path(tempfile.mkdtemp(prefix="repository-build-"))

    try:
        for mod in modules:
            name = mod.get("name", "unknown")
            repository = mod.get("repository", "")
            ref = mod.get("ref", "")
            description = mod.get("description", "")
            version = mod.get("version", "0.0.0")
            tags = mod.get("tags", [])
            plugin_path = mod.get("path", ".")

            if not repository:
                print(f"  Warning: repository module '{name}' missing repository, skipping")
                continue

            ref_err = plugin_registry.repository_ref_error(ref)
            if ref_err:
                print(f"  Warning: repository module '{name}' invalid ref: {ref_err}")
                continue

            clone_dest = tmp / name
            try:
                subprocess.run(
                    ["git", "clone", "--quiet", "--no-checkout", repository, str(clone_dest)],
                    check=True, capture_output=True, text=True, timeout=120,
                )
                subprocess.run(
                    ["git", "checkout", "--quiet", plugin_registry.normalize_repository_ref(ref)],
                    check=True, capture_output=True, text=True, cwd=clone_dest, timeout=30,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                print(f"  Warning: failed to clone '{name}': {exc}")
                continue

            plugin_dir = clone_dest / plugin_path
            license_id = detect_repo_license(clone_dest, plugin_path)
            skills = parse_skills(str(plugin_dir))

            # Read catalog from the cloned source repo
            cat_bundle, cat_warns = bundle_catalog_for_site(plugin_path, clone_dest)
            for w in cat_warns:
                print(f"  ⚠️  {w}")

            maturity = (cat_bundle.get("maturity") or "").strip().upper() if cat_bundle else ""
            if maturity and maturity != plugin_registry.DOCS_MATURITY_PUBLISH:
                print(f"  ⚠️  Skipping '{name}': maturity is {maturity!r} (not GREEN)")
                continue

            # README fallback: read content so the UI can show it when catalog is absent
            readme_path = plugin_dir / "README.md"
            readme_content = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else None

            # MCP servers: parse from cloned content; fix plugin field to use module name
            mcp_servers = parse_mcp_file(str(plugin_dir))
            for s in mcp_servers:
                s["plugin"] = name

            plugin_entry = {
                "name": name,
                "path": repository,
                "repository": repository,
                "ref": plugin_registry.normalize_repository_ref(ref)[:12],
                "icon": mod.get("icon", ""),
                "plugin": {
                    "name": name,
                    "title": mod.get("title") or name.replace("-", " ").title(),
                    "version": version,
                    "description": description,
                    "author": {"name": "External"},
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
            if cat_bundle is not None:
                plugin_entry["collection"] = cat_bundle
            # Enrich with eval reports from the cloned source repo before cleanup
            apply_eval_enrichment([plugin_entry], clone_dest)
            plugins.append(plugin_entry)
            catalog_status = "with catalog" if cat_bundle else "README only"
            mcp_status = f", {len(mcp_servers)} MCP server(s)" if mcp_servers else ""
            print(f"  ✓ '{name}': {len(skills)} skill(s) from {repository} ({catalog_status}{mcp_status})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return plugins


def generate_plugin_data() -> List[Dict[str, Any]]:
    """
    Generate plugin data for all agentic plugins.

    Returns:
        List of plugin dictionaries
    """
    plugins = []

    repository_plugins = load_repository_plugins()
    if repository_plugins:
        plugins.extend(repository_plugins)
        print(f"✓ Added {len(repository_plugins)} marketplace plugin(s)")

    return plugins


if __name__ == '__main__':
    # Test the script
    print("Parsing agentic collections...")
    print()

    plugins = generate_plugin_data()

    print()
    print(f"Found {len(plugins)} collections total")
    print()
    print("Summary:")
    for plugin_entry in plugins:
        plugin = plugin_entry['plugin']
        title = plugin.get('title', plugin['name'])
        print(f"  • {title} v{plugin['version']}")
        print(f"    ({plugin['name']})")
        print(f"    Skills: {len(plugin_entry['skills'])}, Agents: {len(plugin_entry['agents'])}, Docs: {len(plugin_entry['docs'])}")
