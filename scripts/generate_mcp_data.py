#!/usr/bin/env python3
"""
Parse pack MCP configs (hub ``mcp.json``, authoring ``mcps.json`` fallback).
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

MCP_HUB_FILENAME = "mcp.json"
MCP_AUTHORING_FILENAME = "mcps.json"
MCP_DEPRECATED = ".mcp.json"

HTTP_TYPES = {"http", "streamable-http"}


def extract_env_vars(env_dict: Dict[str, str]) -> List[str]:
    """
    Extract environment variable names from ${VAR} format.

    Args:
        env_dict: Dictionary of environment variable configurations

    Returns:
        List of environment variable names
    """
    env_vars = []

    for key, value in env_dict.items():
        # Check if value is in ${VAR} format
        if isinstance(value, str):
            match = re.match(r'^\$\{([A-Z_][A-Z0-9_]*)\}$', value)
            if match:
                # Extract the variable name
                env_vars.append(match.group(1))
            else:
                # If it's a literal value (not ${VAR}), use the key name
                env_vars.append(key)
        else:
            # For non-string values, use the key name
            env_vars.append(key)

    return sorted(set(env_vars))


def extract_header_env_vars(headers: Dict[str, str]) -> List[str]:
    """
    Extract environment variable names from header values.

    Args:
        headers: Dictionary of HTTP headers

    Returns:
        List of environment variable names found in headers
    """
    env_vars = []
    for key, value in headers.items():
        if isinstance(value, str):
            # Extract ${VAR} patterns from header values
            matches = re.findall(r'\$\{([A-Z_][A-Z0-9_]*)\}', value)
            env_vars.extend(matches)
    return env_vars


def _mcp_config_path(pack_path: Path) -> Path | None:
    hub = pack_path / MCP_HUB_FILENAME
    if hub.is_file():
        return hub
    authoring = pack_path / MCP_AUTHORING_FILENAME
    if authoring.is_file():
        return authoring
    return None


def parse_mcp_file(pack_dir: str) -> List[Dict[str, Any]]:
    """
    Parse ``mcp.json`` (hub) or ``mcps.json`` (authoring fallback).

    ``stdio`` is treated as command-based. ``streamable-http`` is treated as
    HTTP so the site UI can reuse the existing remote-server cards.

    Args:
        pack_dir: Filesystem path to the pack directory

    Returns:
        List of MCP server configurations
    """
    pack_path = Path(pack_dir)
    deprecated_path = pack_path / MCP_DEPRECATED
    mcp_file = _mcp_config_path(pack_path)

    if deprecated_path.exists() and mcp_file is None:
        print(
            f"Warning: {pack_dir}/{MCP_DEPRECATED} is deprecated and will be ignored; "
            f"use {MCP_HUB_FILENAME} or {MCP_AUTHORING_FILENAME}"
        )

    if mcp_file is None:
        return []

    try:
        with open(mcp_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        servers = []

        for server_name, server_config in config.get('mcpServers', {}).items():
            if not isinstance(server_config, dict):
                continue
            raw_type = str(server_config.get('type') or 'command').strip().lower()
            is_http = raw_type in HTTP_TYPES
            site_type = 'http' if is_http else 'command'

            server = {
                'name': server_name,
                'pack': pack_dir,
                'type': site_type,
                'transport': raw_type,
                'description': server_config.get('description', ''),
                'security': server_config.get('security', {}),
            }

            if is_http:
                server['url'] = server_config.get('url', '')
                server['headers'] = server_config.get('headers', {})
                env_vars = extract_env_vars(server_config.get('env', {}))
                header_env_vars = extract_header_env_vars(server_config.get('headers', {}))
                server['env'] = sorted(set(env_vars + header_env_vars))
                server['command'] = ''
                server['args'] = []
            else:
                server['command'] = server_config.get('command', '')
                server['args'] = server_config.get('args', [])
                server['env'] = extract_env_vars(server_config.get('env', {}))
                server['url'] = ''
                server['headers'] = {}

            servers.append(server)

        return servers

    except Exception as e:
        print(f"Warning: Failed to parse {mcp_file}: {e}")
        return []


def load_custom_mcp_data() -> Dict[str, Any]:
    """
    Load custom MCP data from docs/mcp.json.

    Returns:
        Dictionary mapping server names to custom data (repository, tools)
    """
    custom_data_file = Path('docs/mcp.json')

    if not custom_data_file.exists():
        print("Warning: docs/mcp.json not found, skipping custom data")
        return {}

    try:
        with open(custom_data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load docs/mcp.json: {e}")
        return {}


def _merge_custom_data(server: Dict[str, Any], custom_data: Dict[str, Any]) -> None:
    """Merge docs/mcp.json metadata into a server dict in place."""
    server_name = server['name']
    custom = custom_data.get(server_name, {})
    server['repository'] = custom.get('repository', '')
    server['tools'] = custom.get('tools', [])
    server['title'] = custom.get('title', server_name)
    server['tier'] = custom.get('tier', 'Official')
    server['owner'] = custom.get('owner', 'Red Hat')


def generate_mcp_data(pack_data: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    """
    Generate MCP server data from pack_data (marketplace packs with mcp_servers_raw)
    merged with custom metadata from docs/mcp.json.

    Args:
        pack_data: List of pack dicts from generate_pack_data(); each may carry
                   ``mcp_servers_raw`` parsed from hub ``mcp.json``.

    Returns:
        List of MCP server dictionaries
    """
    mcp_servers = []
    custom_data = load_custom_mcp_data()

    for pack in (pack_data or []):
        servers = list(pack.get("mcp_servers_raw") or [])
        for server in servers:
            _merge_custom_data(server, custom_data)
        mcp_servers.extend(servers)
        if servers:
            print(f"✓ {pack.get('name', '?')}: {len(servers)} MCP server(s)")

    return mcp_servers


if __name__ == '__main__':
    from generate_pack_data import generate_pack_data
    print("Parsing MCP server configurations...")
    print()

    servers = generate_mcp_data(generate_pack_data())

    print()
    print(f"Found {len(servers)} MCP servers total")
    print()
    print("Summary:")
    for server in servers:
        print(f"  • {server['name']} (from {server['pack']})")
        print(f"    Type: {server['type']}")

        if server['type'] == 'http':
            print(f"    URL: {server['url']}")
            if server['headers']:
                print(f"    Headers: {', '.join(server['headers'].keys())}")
        else:
            print(f"    Command: {server['command']}")

        if server['env']:
            print(f"    Env vars: {', '.join(server['env'])}")

        if server['security']:
            print(f"    Security: {server['security'].get('isolation', 'N/A')}")
        print()
