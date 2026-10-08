#!/usr/bin/env python3
"""
Validate that both command-based and HTTP MCP servers are parsed correctly.
"""

from generate_mcp_data import generate_mcp_data
from generate_pack_data import generate_pack_data


def validate_mcp_types():
    """
    Validate MCP server type detection and parsing.
    """
    servers = generate_mcp_data(generate_pack_data())

    print("🔍 Validating MCP Server Types...\n")

    command_servers = [s for s in servers if s['type'] == 'command']
    http_servers = [s for s in servers if s['type'] == 'http']

    print(f"✓ Found {len(command_servers)} command-based server(s)")
    print(f"✓ Found {len(http_servers)} HTTP remote server(s)\n")

    # Validate command-based servers
    print("📦 Command-based Servers:")
    for server in command_servers:
        assert server['command'], f"Missing command for {server['name']}"
        assert server['url'] == '', f"URL should be empty for command server {server['name']}"
        assert server['headers'] == {}, f"Headers should be empty for command server {server['name']}"
        print(f"  ✓ {server['name']}: {server['command']}")

    print()

    # Validate HTTP servers
    print("🌐 HTTP Remote Servers:")
    for server in http_servers:
        assert server['url'], f"Missing URL for {server['name']}"
        assert server['command'] == '', f"Command should be empty for HTTP server {server['name']}"
        assert server['args'] == [], f"Args should be empty for HTTP server {server['name']}"
        print(f"  ✓ {server['name']}: {server['url']}")

        if server['headers']:
            print(f"    Headers: {', '.join(server['headers'].keys())}")

    print()
    print("✅ All validations passed!")
    return True


if __name__ == '__main__':
    validate_mcp_types()
