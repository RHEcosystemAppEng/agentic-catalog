# AGENTS.md

Guidance for AI coding assistants working in this repository.

## What This Repository Is

This is the **published catalog hub** for Red Hat agentic collections. It is not a skills authoring repo.

1. **Lola marketplace** — `marketplace/rh-agentic-collection.yml` lists packs with hub `repository`, `path` (`plugins/redhat/<pack>`), and pinned `ref` (hub commit SHA). Users: `lola market add` the raw YAML on `main`, then `lola install -f <pack-name>`.
2. **Claude Code marketplace** — `claude-marketplace/marketplace.json` lists the same packs as `git-subdir` sources.
3. **Website** — `docs/` is the static site. `make generate` reads **this checkout only** (no `git clone`).

Authoring stays in source repos (e.g. [agentic-plugins](https://github.com/RHEcosystemAppEng/agentic-plugins)). P6 publishes pack trees here and writes Soundcheck fields onto Lola modules.

## Repository Structure

```
agentic-catalog/
├── plugins/redhat/<pack>/         # Hub payload (skills, mcp.json, README, plugin.json)
├── marketplace/
│   └── rh-agentic-collection.yml  # Single source of truth for pack discovery
├── claude-marketplace/
│   └── marketplace.json
├── docs/                          # Static site (GitHub Pages)
└── scripts/                       # Checkout-only generate
```

`.catalog/` and `eval/` are **authoring-only**. P6 strips them; they are not on the hub and are not fetched at generate time.

## How the Build Works

`make generate` runs `scripts/build_website.py`, which:

1. Reads `marketplace/rh-agentic-collection.yml`
2. Includes a module only if `repo_root / module.path` exists (e.g. `plugins/redhat/rh-sre`)
3. Reads `skills/*/SKILL.md`, `README.md`, and hub **`mcp.json`**
4. Attaches `soundcheck_levels_summary` and `mcp_evaluations` from the module (Soundcheck, not ABEval)
5. Attaches `install` links (GitHub tree, Lola, Claude marketplace)
6. Writes `docs/data.json` and `docs/collections/<pack>.html`

Do **not** add generate-time clones of GitLab authoring, GitHub agentic-plugins, or this hub.

## Marketplace File

`marketplace/rh-agentic-collection.yml` controls which packs appear. Hub-published modules:

| Field | Purpose |
|-------|---------|
| `name` | Pack identifier |
| `repository` | Hub git URL (`agentic-catalog`) |
| `path` | Hub subdirectory, e.g. `plugins/redhat/rh-sre` |
| `ref` | 40-char **hub** commit SHA |
| `content_hash` | Pack payload hash from P6 |
| `soundcheck_levels_summary` | Skill-track Soundcheck (Foundational / Trusted / Certified) |
| `mcp_evaluations[]` | Per-MCP Compass scorecard (Lead / Bronze / Silver / Gold). Do **not** join `name` onto `mcp.json` keys. |

Modules still pointing at `agentic-plugins` with a path that is not on disk are **skipped**.

## Scripts

| Script | Purpose | Invoked by |
|--------|---------|------------|
| `build_website.py` | Orchestrates the full build | `make generate` |
| `generate_pack_data.py` | Hub-local pack/skill/README/`mcp.json` | build |
| `generate_mcp_data.py` | Parses hub `mcp.json` (`stdio` / `streamable-http`) | build |
| `marketplace_eval_enrichment.py` | Soundcheck + MCP scorecards from YAML | build |
| `install_links.py` | GitHub / Lola / Claude install metadata | build |
| `generate_collection_pages.py` | Per-pack HTML | build |
| `pack_registry.py` | Marketplace discovery (`get_union_pack_dirs`) | build |
| `eval_site_enrichment.py` | Unused (ABEval; hub has no `eval/`) | — |
| `catalog_site_bundle.py` | Unused (no `.catalog` on hub) | — |
| `test_local.sh` | Automated validation | `make test` |

## Key Rules

- **Marketplace is the single source of truth** for which packs appear.
- **Generated files are read-only.** `docs/data.json` and `docs/collections/*.html` are rebuilt every run.
- **No skills development here.** Change skills in the authoring repo; P6 republishes the hub tree.
- **Eval on the site is Soundcheck** from marketplace YAML. Do not use `recommendation` (P3 constant) or ABEval trial counts for badges.
- **Security.** DOM updates in `app.js` use `textContent` / `createElement` — never `innerHTML` with external data.

## CI

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `validate.yml` | PR; push to `main` or `rc/v1.0.0` | `make test` |
| `deploy-pages.yml` | Push to **`main` only** | `make generate`, deploy `docs/` |

Do not deploy Pages from `rc/v1.0.0`. Expand Pages `paths` includes `plugins/**` and `claude-marketplace/**`.
