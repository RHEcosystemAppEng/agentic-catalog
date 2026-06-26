#!/usr/bin/env python3
"""
Parse mcps.json files and extract MCP server configurations.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

MCP_FILENAME = "mcps.json"
MCP_DEPRECATED = ".mcp.json"


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


def parse_mcp_file(pack_dir: str) -> List[Dict[str, Any]]:
    """
    Parse mcps.json file from a pack directory.
    Supports both command-based and HTTP-based MCP servers.
    Errors if deprecated .mcp.json exists (must be renamed to mcps.json).

    Args:
        pack_dir: Name of the pack directory

    Returns:
        List of MCP server configurations
    """
    pack_path = Path(pack_dir)
    deprecated_path = pack_path / MCP_DEPRECATED
    mcp_file = pack_path / MCP_FILENAME

    if deprecated_path.exists():
        print(f"Warning: {pack_dir}/{MCP_DEPRECATED} is deprecated and will be ignored; rename to {MCP_FILENAME}")

    if not mcp_file.exists():
        return []

    try:
        with open(mcp_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        servers = []

        # Extract each MCP server
        for server_name, server_config in config.get('mcpServers', {}).items():
            # Detect server type
            server_type = server_config.get('type', 'command')

            # Base server configuration
            server = {
                'name': server_name,
                'pack': pack_dir,
                'type': server_type,
                'description': server_config.get('description', ''),
                'security': server_config.get('security', {})
            }

            # Extract type-specific fields
            if server_type == 'http':
                # HTTP-based remote server
                server['url'] = server_config.get('url', '')
                server['headers'] = server_config.get('headers', {})

                # Extract env vars from both env dict and headers
                env_vars = extract_env_vars(server_config.get('env', {}))
                header_env_vars = extract_header_env_vars(server_config.get('headers', {}))
                server['env'] = sorted(set(env_vars + header_env_vars))

                # Command and args are not applicable for HTTP servers
                server['command'] = ''
                server['args'] = []
            else:
                # Command-based server (default)
                server['command'] = server_config.get('command', '')
                server['args'] = server_config.get('args', [])
                server['env'] = extract_env_vars(server_config.get('env', {}))

                # URL and headers are not applicable for command servers
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
                   ``mcp_servers_raw`` parsed during the clone phase.

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
