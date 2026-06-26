# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is the **unified catalog and marketplace** for Red Hat agentic collections. It aggregates skills, MCP server configurations, and agentic packs from multiple source repositories into a single, browsable catalog served through [Lola](https://github.com/LobsterTrap/lola) and the [agentskills.io](https://agentskills.io) website.

**This is NOT a skills development repository.** No skills are authored or maintained here. Skills live in their own source repositories (e.g., [agentic-collections-skills](https://github.com/RHEcosystemAppEng/agentic-collections-skills)). An internal process fetches content from those repos, evaluates it with its own scorecard, and assembles the catalog automatically.

## Repository Structure

```
agentic-collections-catalog/
├── marketplace/                 # Lola marketplace definition
│   └── rh-agentic-collection.yml  # Module registry — what users install via `lola install -f`
├── catalog/                     # Collection schema for validation
│   └── schema.yaml
├── docs/                        # Website source (agentskills.io)
│   ├── index.html               # Landing page
│   ├── app.js                   # Application logic
│   ├── styles.css               # Styling
│   ├── data.json                # Generated catalog data (skills, packs, MCPs)
│   ├── mcp.json                 # MCP server metadata
│   └── collections/             # Generated per-pack HTML pages
├── scripts/                     # Catalog build and maintenance scripts

├── README.md
└── LICENSE
```

## How the Catalog Works

### Data Flow

```
Skills repos (multiple)          Internal process          This repo
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│ agentic-collections-│     │ Fetch skills repos    │     │ marketplace/        │
│ skills/             │────>│ Evaluate & score      │────>│ docs/ (website)     │
│   rh-sre/           │     │ Build catalog data    │     │ data.json           │
│   ocp-admin/        │     │ Generate website      │     │ mcp.json            │
│   ...               │     └──────────────────────┘     └─────────────────────┘
├─────────────────────┤
│ other-skills-repo/  │────> (same process)
└─────────────────────┘
```

Each skills repo contains packs with `.catalog/` metadata that describes its content. The internal process reads that metadata, applies its own evaluation and scoring, and publishes the results here.

### Marketplace (Lola)

`marketplace/rh-agentic-collection.yml` is the Lola module registry. Users consume it with:

```bash
lola market add rh-agentic-collections <url-to-marketplace-yml>
lola install -f rh-sre
```

This file defines which packs are available, their versions, and where to fetch them.

### Website (agentskills.io)

The `docs/` directory contains the static site served at agentskills.io. Key files:

- `data.json` — Generated catalog data aggregating all packs, skills, and MCP servers
- `mcp.json` — MCP server metadata and tool descriptions
- `collections/*.html` — Per-pack detail pages

### Collection Schema

- `catalog/schema.yaml` — JSON Schema that defines the structure of `.catalog/collection.yaml` files in skills repos

## Scripts

Scripts in `scripts/` support catalog build and maintenance:

| Script | Purpose |
|--------|---------|
| `build_website.py` | Generate `docs/data.json` from pack data |
| `generate_pack_data.py` | Extract pack metadata for the website |
| `generate_mcp_data.py` | Extract MCP server data for the website |
| `generate_collection_pages.py` | Generate per-pack HTML pages |
| `catalog_site_bundle.py` | Resolve `.catalog/` fragment refs for site embedding |
| `check_site.py` | Interactive site summary and manual testing checklist |
| `test_local.sh` | Automated site verification (data.json, HTML, XSS, credentials) |
| `validate_mcp_types.py` | Validate MCP server type parsing (command vs HTTP) |
| `eval_site_enrichment.py` | Enrich catalog with evaluation data |
| `pack_registry.py` | Discover packs from the marketplace (single source of truth) |

## Key Considerations

### No CI in This Repo

This repository has no GitHub Actions workflows. The internal process that builds the catalog handles all validation, evaluation, and deployment.

### No Skills Development

If you need to create or modify skills, work in the appropriate skills source repository, not here. This repo only contains the infrastructure to aggregate and present skills.

### Catalog Data is Generated

Files like `docs/data.json` and `docs/collections/*.html` are generated artifacts. They are rebuilt by the internal process and should not be edited manually.

### Schema Changes

If the structure of `.catalog/collection.yaml` needs to change, update `catalog/schema.yaml` here, then coordinate with skills repos to update their `.catalog/` directories accordingly.
