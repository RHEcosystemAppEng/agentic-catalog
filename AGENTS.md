# AGENTS.md

Guidance for AI coding assistants working in this repository.

## What This Repository Is

This is the **catalog and marketplace** for Red Hat agentic collections. It serves two purposes:

1. **Lola marketplace** — `marketplace/rh-agentic-collection.yml` declares which skill packs are available and where to fetch them. Users install packs with `lola install -f <pack-name>`.
2. **agentskills.io website** — the `docs/` directory is the static site. The scripts in `scripts/` build it by cloning each pack's source repo and extracting metadata.

**No skills are authored or stored here.** Skills live in their own source repos (e.g., [agentic-collections-skills](https://github.com/RHEcosystemAppEng/agentic-collections-skills)). This repo only aggregates and presents them.

## Repository Structure

```
agentic-catalog/
├── marketplace/
│   └── rh-agentic-collection.yml  # Single source of truth for pack discovery
├── docs/                          # Static site (agentskills.io)
│   ├── index.html                 # SPA entry point
│   ├── app.js                     # Rendering and search logic (XSS-safe, no innerHTML)
│   ├── styles.css                 # Red Hat-themed styling
│   ├── data.json                  # Generated — do not edit manually
│   ├── mcp.json                   # MCP server metadata — do not edit manually
│   └── collections/               # Generated per-pack HTML pages
└── scripts/                       # Build and verification scripts
```

## How the Build Works

`make generate` runs `scripts/build_website.py`, which:

1. Reads `marketplace/rh-agentic-collection.yml` to get the list of packs
2. For each pack: `git clone` its source repo into a temp directory
3. Reads `.catalog/collection.yaml` (if present) for metadata and maturity
4. Skips packs whose catalog declares a non-GREEN maturity; absent catalog → assumed GREEN
5. Reads `skills/*/SKILL.md` frontmatter, README, and `mcps.json` from the clone
6. Writes `docs/data.json` and generates `docs/collections/<pack>.html`

The clones are ephemeral (deleted after each build). Nothing from external repos is committed here.

> **Eval data lives in source repos, not here.** `eval_site_enrichment.py` reads `eval/<pack>/<skill>/report.json` from the *cloned* source repo (e.g. `agentic-collections-skills/eval/rh-sre/remediation/report.json`). There is no `eval/` directory in this catalog repo — looking for eval files here will always find nothing.

## Marketplace File

`marketplace/rh-agentic-collection.yml` is the **only** place that controls which packs appear on the site. Each module entry carries:

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | yes | Pack identifier (used in URLs and filenames) |
| `repository` | yes | Git URL to clone |
| `path` | yes | Subdirectory within the repo (`.` for root) |
| `version` | yes | Displayed version |
| `description` | yes | Short description shown on cards |
| `title` | yes | Display name shown on cards |
| `icon` | recommended | Emoji or HTTPS URL to an image |
| `tags` | optional | Filter tags |
| `ref` | optional | 40-char commit SHA to pin; absent = main branch |

Do not add packs to `docs/data.json` or any other file directly. Add them to the marketplace YAML.

## Scripts

| Script | Purpose | Invoked by |
|--------|---------|------------|
| `build_website.py` | Orchestrates the full build | `make generate` |
| `generate_pack_data.py` | Clones repos, extracts pack/skill metadata | build |
| `generate_mcp_data.py` | Extracts MCP server configs from `mcps.json` | build |
| `generate_collection_pages.py` | Renders per-pack HTML pages | build |
| `catalog_site_bundle.py` | Resolves `.catalog/` fragment `#ref` pointers | build |
| `eval_site_enrichment.py` | Attaches ABEval report summaries to skills | build |
| `pack_registry.py` | Marketplace-driven pack discovery utilities | build |
| `check_site.py` | Interactive manual verification of `data.json` | manual |
| `test_local.sh` | Automated validation (JSON, HTML, XSS, credentials) | `make test` |
| `validate_mcp_types.py` | Sanity-checks MCP server type parsing | manual |

## Key Rules

- **Marketplace is the single source of truth.** Do not add packs, icons, or titles anywhere else.
- **Generated files are read-only.** `docs/data.json`, `docs/mcp.json`, and `docs/collections/*.html` are rebuilt on every run — manual edits will be overwritten.
- **No skills development here.** To create or modify skills, work in the appropriate skills source repo.
- **Schema changes need coordination.** Updating `.catalog/collection.yaml` in skills repos requires consistent field usage across all packs.
- **Security.** All DOM manipulation in `app.js` uses `textContent` and `createElement` — never `innerHTML` with external data.

## CI

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `validate.yml` | Push / PR | Runs `make test` (→ `test_local.sh`) |
| `deploy-pages.yml` | Push to main | Runs `make generate`, deploys `docs/` to GitHub Pages |
