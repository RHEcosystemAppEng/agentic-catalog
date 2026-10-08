# Agentic Catalog

Published **hub** for Red Hat agentic skill collections: Lola marketplace, Claude Code marketplace, pack trees under `plugins/redhat/`, and the GitHub Pages website.

Skills are **authored** in source repositories such as [agentic-plugins](https://github.com/RHEcosystemAppEng/agentic-plugins). An internal pipeline (plugin-pipeline P6) evaluates packs and publishes them onto this hub (`rc/v1.0.0` for the ecosystem channel). The live website deploys from **`main`** after merge.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Validate Catalog](https://github.com/RHEcosystemAppEng/agentic-catalog/actions/workflows/validate.yml/badge.svg)](https://github.com/RHEcosystemAppEng/agentic-catalog/actions/workflows/validate.yml)
[![Deploy GitHub Pages](https://github.com/RHEcosystemAppEng/agentic-catalog/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/RHEcosystemAppEng/agentic-catalog/actions/workflows/deploy-pages.yml)

---

## Structure

```
agentic-catalog/
├── plugins/redhat/              # Published pack trees (hub payload)
├── marketplace/
│   └── rh-agentic-collection.yml  # Lola modules (path, ref, Soundcheck)
├── claude-marketplace/
│   └── marketplace.json         # Claude Code git-subdir listings
├── docs/                        # GitHub Pages site
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── data.json                # Generated — do not edit
│   ├── mcp.json                 # MCP enrichment metadata
│   └── collections/             # Generated per-pack HTML
├── scripts/                     # Checkout-only site generate
└── Makefile
```

---

## Install

Three ways to consume a pack from this hub (no ZIP releases on the ecosystem channel).

### 1. Direct (GitHub)

Open the pack directory at the commit pinned in the marketplace `ref`, for example:

`https://github.com/RHEcosystemAppEng/agentic-catalog/tree/<ref>/plugins/redhat/<pack>`

Clone this repository and use the same subdirectory.

### 2. Lola

```bash
lola market add rh-agentic-collections https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-catalog/main/marketplace/rh-agentic-collection.yml
lola install -f <pack-name>
```

Use branch **`main`** (the published hub). P6 may still land on `rc/v1.0.0` until that work is merged.

### 3. Claude Code marketplace

Marketplace file:

`https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-catalog/main/claude-marketplace/marketplace.json`

Add that marketplace in Claude Code, then install the plugin by name (each entry is a `git-subdir` of `plugins/redhat/<pack>`).

---

## Usage (site maintainers)

```bash
# Install dependencies
make install

# Generate docs/data.json and collection pages from THIS checkout
make generate

# Generate + verify site
make test

# Start local server at http://localhost:8000
make serve
```

`make generate` does **not** clone other repositories. It reads `marketplace/rh-agentic-collection.yml`, `plugins/redhat/*`, `claude-marketplace/marketplace.json`, pack `README.md` / `mcp.json` / `skills/`. Modules whose `path` is missing on disk are skipped.

Eval on the site is **Soundcheck** from the marketplace YAML (`soundcheck_levels_summary` and `mcp_evaluations`), not ABEval `eval/` reports.

---

## How It Works

```
Authoring (GitLab)               Pipeline                      This hub
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│ agentic-plugins     │     │ Fetch, score,        │     │ plugins/redhat/     │
│ <pack>/skills/      │────>│ assemble, publish    │────>│ marketplace/        │
│                     │     │ (P6 ecosystem)       │     │ claude-marketplace/ │
└─────────────────────┘     └──────────────────────┘     │ docs/ (Pages)       │
                                                         └─────────────────────┘
```

GitHub Pages: develop and validate on `rc/v1.0.0`; merge into `main` to publish the site.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

**Maintained by:** [Red Hat Ecosystem Engineering](https://github.com/RHEcosystemAppEng)
