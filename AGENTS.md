# AGENTS.md

Guidance for AI coding assistants working in this repository.

## What This Repository Is

This is the **published catalog hub** for Red Hat agentic collections. It is not a skills authoring repo.

1. **Lola marketplace** — `marketplace/rh-agentic-collection.yml` lists plugins with hub `repository`, `path` (`plugins/redhat/<plugin>`), and pinned `ref` (hub commit SHA). Users: `lola market add` the raw YAML, then `lola install -f <plugin-name>`.
2. **Claude Code marketplace** — `.claude-plugin/marketplace.json` lists the same plugins as `git-subdir` sources.
3. **Codex / ChatGPT plugins marketplace** — `.agents/plugins/marketplace.json` lists the same plugins in Codex's schema (`./`-prefixed `git-subdir` paths, `policy`, `category`).
4. **Cursor marketplace** — `.cursor-plugin/marketplace.json` lists the same plugins with **relative** `source` paths (not `git-subdir`). Register the repo with `cursor-agent plugin marketplace add`; install plugins via Customize or `/plugin` (no `plugin install` CLI yet).
5. **Website** — `docs/` is the static site. `make generate` reads **this checkout only** (no `git clone`).

Authoring stays in source repos (e.g. [agentic-plugins](https://github.com/RHEcosystemAppEng/agentic-plugins)). The catalog publish automation copies plugin trees here and writes Soundcheck fields onto Lola modules.

## Repository Structure

```
agentic-catalog/
├── plugins/redhat/<plugin>/         # Hub payload (skills, mcp.json, README, plugin.json)
├── marketplace/
│   └── rh-agentic-collection.yml  # Single source of truth for plugin discovery
├── .claude-plugin/
│   └── marketplace.json           # Claude Code catalog
├── .agents/plugins/
│   └── marketplace.json           # Codex / ChatGPT plugins catalog
├── .cursor-plugin/
│   └── marketplace.json           # Cursor catalog
├── docs/                          # Static site (GitHub Pages)
└── scripts/                       # Checkout-only generate
```

`.catalog/` and `eval/` exist only in **authoring** repositories. They are not part of this published hub, and `make generate` does not read them.

## How the Build Works

`make generate` runs `scripts/build_website.py`, which:

1. Reads `marketplace/rh-agentic-collection.yml`
2. Includes a module only if `repo_root / module.path` exists (e.g. `plugins/redhat/rh-sre`)
3. Reads `skills/*/SKILL.md`, `README.md`, and hub **`mcp.json`**
4. Attaches `soundcheck_levels_summary` and `mcp_evaluations` from the module (Soundcheck, not ABEval)
5. Attaches `install` links (GitHub tree, Lola, Claude, Codex, Cursor — see `install_links.py`)
6. Writes `docs/data.json` and `docs/collections/<plugin>.html`

Do **not** add generate-time clones of GitLab authoring, GitHub agentic-plugins, or this hub.

## Marketplace File

`marketplace/rh-agentic-collection.yml` controls which plugins appear. Hub-published modules:

| Field | Purpose |
|-------|---------|
| `name` | Plugin identifier |
| `repository` | Hub git URL (`agentic-catalog`) |
| `path` | Hub subdirectory, e.g. `plugins/redhat/rh-sre` |
| `ref` | 40-char **hub** commit SHA |
| `content_hash` | Plugin payload hash set by the catalog publish automation |
| `soundcheck_levels_summary` | Skill-track Soundcheck (Foundational / Trusted / Certified) |
| `mcp_evaluations[]` | Per-MCP Compass scorecard (Lead / Bronze / Silver / Gold). Do **not** join `name` onto `mcp.json` keys. |

Modules still pointing at `agentic-plugins` with a path that is not on disk are **skipped**.

## Scripts

| Script | Purpose | Invoked by |
|--------|---------|------------|
| `build_website.py` | Orchestrates the full build | `make generate` |
| `generate_plugin_data.py` | Hub-local plugin/skill/README/`mcp.json` | build |
| `generate_mcp_data.py` | Parses hub `mcp.json` (`stdio` / `streamable-http`) | build |
| `marketplace_eval_enrichment.py` | Soundcheck + MCP scorecards from YAML | build |
| `install_links.py` | GitHub / Lola / Claude / Codex / Cursor install metadata | build |
| `generate_collection_pages.py` | Per-plugin HTML | build |
| `plugin_registry.py` | Marketplace discovery (`get_union_plugin_dirs`) | build |
| `eval_site_enrichment.py` | Unused (ABEval; hub has no `eval/`) | — |
| `catalog_site_bundle.py` | Unused (no `.catalog` on hub) | — |
| `test_local.sh` | Automated validation | `make test` |

## Key Rules

- **Marketplace is the single source of truth** for which plugins appear.
- **Generated files are read-only and gitignored.** `docs/data.json` and `docs/collections/*.html` are rebuilt every run (`make generate`) and never committed.
- **No skills development here.** Change skills in the authoring repo; the catalog publish automation republishes the hub tree.
- **Eval on the site is Soundcheck** from marketplace YAML. Do not use `recommendation` (a legacy pipeline field) or ABEval trial counts for badges.
- **`install_links.py` builds all four channels.** `install.codex` and `install.cursor` read `.agents/plugins/marketplace.json` and `.cursor-plugin/marketplace.json` the same way `install.claude` reads `.claude-plugin/marketplace.json`. If a marketplace file is missing on disk, the loader returns `{}` and the install block still falls back to `hub_path` — it does not raise.
- **Security.** DOM updates in `app.js` use `textContent` / `createElement` — never `innerHTML` with external data.

## CI

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `validate.yml` | PR; push to `main` or `rc/v1.0.0` | `make test` |
| `deploy-pages.yml` | Push to **`main` only** | `make generate`, deploy `docs/` |

Do not deploy Pages from `rc/v1.0.0`. Pages `paths` filter includes `plugins/**`, `marketplace/**`, `.claude-plugin/**`, `.agents/**`, and `.cursor-plugin/**`.

## For Maintainers (optional context)

Hub contents are produced by Red Hat's internal plugin catalog pipeline (`plugin-pipeline`, not in this repo). Routing from authoring markets to this hub lives in that repo's `policy/routing-mapping.yaml`. This detail is not needed to work in `agentic-catalog` itself — only link to it if you are debugging why a publish did or didn't land here.
