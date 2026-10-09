#!/usr/bin/env python3
"""
Build the documentation website by combining plugin data and MCP data into data.json.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# Import our data generators
from catalog_site_bundle import bundle_catalog_for_site
from generate_collection_pages import generate_collection_pages
from generate_plugin_data import generate_plugin_data
from generate_mcp_data import generate_mcp_data


def build_website():
    """
    Generate the complete website data file.
    """
    print("🔨 Building documentation website...")
    print()

    # Generate plugin data
    print("📦 Parsing agentic collections...")
    plugin_data = generate_plugin_data()

    root = Path(__file__).resolve().parent.parent

    # Resolve collection catalog for plugins that don't have it from the clone phase
    for plugin in plugin_data:
        if 'collection' not in plugin:
            plugin_name = plugin['name']
            catalog_dir = plugin.get('catalog_dir', plugin_name)
            cat_bundle, cat_warns = bundle_catalog_for_site(catalog_dir, root)
            for w in cat_warns:
                print(f"⚠️  {w}")
            if cat_bundle is not None:
                plugin['collection'] = cat_bundle

    # Keep plugin cards deterministic and alphabetically ordered.
    plugin_data = sorted(plugin_data, key=lambda p: p['name'])

    # Generate MCP server data
    print("🔌 Parsing MCP servers...")
    mcp_data = generate_mcp_data(plugin_data)
    print()

    # Generate static collection pages (fork-compatible UX)
    print("📄 Generating static collection pages...")
    page_count = generate_collection_pages(plugin_data, mcp_data)
    print(f"✅ Generated {page_count} pages in docs/collections/")
    print()

    # Combine into final output
    output = {
        'repository': {
            'name': 'agentic-catalog',
            'owner': 'Red Hat Ecosystem Engineering',
            'description': 'Agentic collections catalog and website for Red Hat platforms and products',
            'url': 'https://github.com/RHEcosystemAppEng/agentic-catalog'
        },
        'plugins': plugin_data,
        'mcp_servers': mcp_data,
        'generated_at': datetime.now(timezone.utc).isoformat()
    }

    # Ensure docs directory exists
    docs_dir = Path('docs')
    docs_dir.mkdir(exist_ok=True)

    # Write data.json
    output_file = docs_dir / 'data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {output_file}")
    print()
    print("📊 Summary:")
    print(f"   • {len(plugin_data)} agentic collections")
    total_skills = sum(len(p['skills']) for p in plugin_data)
    total_agents = sum(len(p['agents']) for p in plugin_data)
    print(f"   • {total_skills} skills")
    print(f"   • {total_agents} agents")
    print(f"   • {len(mcp_data)} MCP servers")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(build_website())
