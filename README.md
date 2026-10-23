# Agentic Catalog

Published **hub** for Red Hat agentic skill collections: plugin trees under `plugins/redhat/`, marketplace listings for Lola, Claude Code, Codex, and Cursor, and the GitHub Pages website.

Skills are **authored** in source repositories such as [agentic-plugins](https://github.com/RHEcosystemAppEng/agentic-plugins). An automated catalog publish process evaluates plugins and pushes them onto this hub (`rc/v1.0.0` for the ecosystem channel, pending merge to `main`). The live website deploys from **`main`** after merge.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Validate Catalog](https://github.com/RHEcosystemAppEng/agentic-catalog/actions/workflows/validate.yml/badge.svg)](https://github.com/RHEcosystemAppEng/agentic-catalog/actions/workflows/validate.yml)
[![Deploy GitHub Pages](https://github.com/RHEcosystemAppEng/agentic-catalog/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/RHEcosystemAppEng/agentic-catalog/actions/workflows/deploy-pages.yml)

---

## Structure

```
agentic-catalog/
├── plugins/redhat/                 # Published plugin trees (hub payload)
├── marketplace/
│   └── rh-agentic-collection.yml   # Lola catalog (path, ref, Soundcheck)
├── .claude-plugin/
│   └── marketplace.json            # Claude Code catalog (git-subdir listings)
├── .agents/plugins/
│   └── marketplace.json            # Codex / ChatGPT plugins catalog
├── .cursor-plugin/
│   └── marketplace.json            # Cursor catalog (relative source paths)
├── docs/                           # GitHub Pages site
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── data.json                  # Generated — do not edit
│   ├── mcp.json                   # MCP enrichment metadata
│   └── collections/               # Generated per-plugin HTML
├── scripts/                        # Checkout-only site generate
└── Makefile
```

---

## Install

Four ways to consume a plugin from this hub (no ZIP releases on the ecosystem channel). Each catalog lists the same packs (e.g. `rh-basic`, `rh-sre`, `rh-virt`, `ocp-admin`); only the wire format and install UX differ.

> **Branch note:** this README and the marketplace files below live on **`rc/v1.0.0`** until that branch is merged to `main`. Use `rc/v1.0.0` in every URL and `--ref` flag until then. After merge, drop `--ref` and swap `rc/v1.0.0` for `main` in raw URLs.

### 1. Direct (GitHub)

Open the plugin directory at the commit pinned in the marketplace `ref`, for example:

`https://github.com/RHEcosystemAppEng/agentic-catalog/tree/rc/v1.0.0/plugins/redhat/<plugin>`

Clone this repository and use the same subdirectory.

### 2. Lola

```bash
lola market add rh-agentic-collections \
  https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-catalog/rc/v1.0.0/marketplace/rh-agentic-collection.yml
lola install -f <plugin-name>
```

### 3. Claude Code marketplace

Marketplace file:

`https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-catalog/rc/v1.0.0/.claude-plugin/marketplace.json`

Add that marketplace in Claude Code, then install the plugin by name (each entry is a `git-subdir` of `plugins/redhat/<plugin>`).

### 4. Codex / ChatGPT plugins

```bash
codex plugin marketplace add https://github.com/RHEcosystemAppEng/agentic-catalog.git --ref rc/v1.0.0
codex plugin add <plugin-name>@ecosystem-plugins
```

The Codex index lives at `.agents/plugins/marketplace.json` — same packs as Claude Code, Codex schema (`git-subdir`, `./`-prefixed paths, `policy`, `category`).

### 5. Cursor

Add this repository (or a local clone on `rc/v1.0.0`) as a marketplace in Cursor. It reads `.cursor-plugin/marketplace.json`, which uses **relative** `source` paths (e.g. `plugins/redhat/rh-basic`) rather than `git-subdir`. Install a plugin by name from that marketplace.

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

`make generate` does **not** clone other repositories. It reads `marketplace/rh-agentic-collection.yml`, `plugins/redhat/*`, `.claude-plugin/marketplace.json`, plugin `README.md` / `mcp.json` / `skills/`. Modules whose `path` is missing on disk are skipped.

Eval on the site is **Soundcheck** from the marketplace YAML (`soundcheck_levels_summary` and `mcp_evaluations`), not ABEval `eval/` reports.

---

## How It Works

```
Authoring                        Catalog publish                This hub
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│ agentic-plugins      │     │ Fetch, score,        │     │ plugins/redhat/      │
│ <plugin>/skills/     │────>│ assemble, publish    │────>│ marketplace/          │
│                      │     │ (ecosystem channel)  │     │ .claude-plugin/       │
└─────────────────────┘     └──────────────────────┘     │ .agents/plugins/      │
                                                           │ .cursor-plugin/       │
                                                           │ docs/ (Pages)         │
                                                           └──────────────────────┘
```

GitHub Pages: develop and validate on `rc/v1.0.0`; merge into `main` to publish the site.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

**Maintained by:** [Red Hat Ecosystem Engineering](https://github.com/RHEcosystemAppEng)
