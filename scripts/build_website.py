#!/usr/bin/env python3
"""
Build the documentation website by combining pack data and MCP data into data.json.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from generate_collection_pages import generate_collection_pages
from generate_pack_data import generate_pack_data
from generate_mcp_data import generate_mcp_data


def build_website():
    """
    Generate the complete website data file from this hub checkout.
    """
    print("🔨 Building documentation website...")
    print()

    print("📦 Parsing agentic collections...")
    pack_data = generate_pack_data()

    pack_data = sorted(pack_data, key=lambda p: p['name'])

    print("🔌 Parsing MCP servers...")
    mcp_data = generate_mcp_data(pack_data)
    print()

    for pack in pack_data:
        pack.pop("mcp_servers_raw", None)

    print("📄 Generating static collection pages...")
    page_count = generate_collection_pages(pack_data, mcp_data)
    print(f"✅ Generated {page_count} pages in docs/collections/")
    print()

    output = {
        'repository': {
            'name': 'agentic-catalog',
            'owner': 'Red Hat Ecosystem Engineering',
            'description': 'Agentic collections catalog and website for Red Hat platforms and products',
            'url': 'https://github.com/RHEcosystemAppEng/agentic-catalog'
        },
        'packs': pack_data,
        'mcp_servers': mcp_data,
        'generated_at': datetime.now(timezone.utc).isoformat()
    }

    docs_dir = Path('docs')
    docs_dir.mkdir(exist_ok=True)

    output_file = docs_dir / 'data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {output_file}")
    print()
    print("📊 Summary:")
    print(f"   • {len(pack_data)} agentic collections")
    total_skills = sum(len(p['skills']) for p in pack_data)
    total_agents = sum(len(p['agents']) for p in pack_data)
    print(f"   • {total_skills} skills")
    print(f"   • {total_agents} agents")
    print(f"   • {len(mcp_data)} MCP servers")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(build_website())
