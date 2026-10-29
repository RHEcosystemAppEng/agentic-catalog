# Agentic Catalog

Published **hub** for Red Hat agentic skill collections: plugin trees under `plugins/redhat/`, marketplace listings for Lola, Claude Code, Codex, and Cursor, and the GitHub Pages website.

Skills are **authored** in source repositories such as [agentic-plugins](https://github.com/RHEcosystemAppEng/agentic-plugins). An automated catalog publish process evaluates plugins and pushes them onto this hub. The live website and all consumer install URLs use the **`main`** branch.

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

Five ways to consume a plugin from this hub (no ZIP releases on the ecosystem channel). Each catalog lists the same packs (e.g. `rh-basic`, `rh-sre`, `rh-virt`, `ocp-admin`); only the wire format and install UX differ. Use branch **`main`** in every URL and `--ref` below.

### 1. Direct (GitHub)

Open the plugin directory at the commit pinned in the marketplace `ref`, for example:

`https://github.com/RHEcosystemAppEng/agentic-catalog/tree/main/plugins/redhat/<plugin>`

Clone this repository on `main` and use the same subdirectory.

### 2. Lola

```bash
lola market add rh-agentic-collections \
  https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-catalog/main/marketplace/rh-agentic-collection.yml
lola install -f <plugin-name>
```

### 3. Claude Code

```bash
claude plugin marketplace add https://github.com/RHEcosystemAppEng/agentic-catalog.git --scope project
claude plugin install <plugin-name>@ecosystem-plugins --scope project
```

Marketplace manifest: `https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-catalog/main/.claude-plugin/marketplace.json`

### 4. Codex / ChatGPT plugins

```bash
codex plugin marketplace add https://github.com/RHEcosystemAppEng/agentic-catalog.git --ref main
codex plugin add <plugin-name>@ecosystem-plugins
```

The Codex index lives at `.agents/plugins/marketplace.json` — same packs as Claude Code, Codex schema (`git-subdir`, `./`-prefixed paths, `policy`, `category`).

### 5. Cursor

Register the hub marketplace from the [Cursor CLI](https://cursor.com/docs/cli/overview) (`cursor-agent`). **Plugin install is UI-only** today — there is no `cursor-agent plugin install` command.

```bash
cursor-agent plugin marketplace add https://github.com/RHEcosystemAppEng/agentic-catalog.git --git-ref main
```

Then install `<plugin-name>` using one of:

- **IDE:** **Customize** in the sidebar → find the plugin from your marketplace → Install (User or Project scope).
- **CLI (interactive):** run `cursor-agent`, type `/plugin`, open **Marketplace**, select the plugin, choose scope.

Manifest: `.cursor-plugin/marketplace.json` on branch **`main`**. See [Cursor plugins docs](https://cursor.com/docs/plugins).

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

GitHub Pages deploys from **`main`**.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

**Maintained by:** [Red Hat Ecosystem Engineering](https://github.com/RHEcosystemAppEng)
