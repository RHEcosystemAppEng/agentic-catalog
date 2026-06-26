# Agentic Collections Catalog

Unified marketplace and website for Red Hat agentic skill collections. This repository aggregates content from skills source repositories and publishes it through [Lola](https://github.com/LobsterTrap/lola) and [agentskills.io](https://agentskills.io).

**This is not a skills development repository.** Skills are authored in source repositories like [agentic-collections-skills](https://github.com/RHEcosystemAppEng/agentic-collections-skills). An internal process fetches, evaluates, and assembles the catalog automatically.

> **Note:** Evaluation reports (`eval/<pack>/<skill>/report.json`) live in the **source skills repos**, not here. This catalog repo contains no `eval/` directory — eval data is read from the temporary clones at build time.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Validate Catalog](https://github.com/RHEcosystemAppEng/agentic-collections-catalog/actions/workflows/validate.yml/badge.svg)](https://github.com/RHEcosystemAppEng/agentic-collections-catalog/actions/workflows/validate.yml)
[![Deploy GitHub Pages](https://github.com/RHEcosystemAppEng/agentic-collections-catalog/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/RHEcosystemAppEng/agentic-collections-catalog/actions/workflows/deploy-pages.yml)

---

## Structure

```
agentic-collections-catalog/
├── marketplace/                 # Lola marketplace definition
│   └── rh-agentic-collection.yml
├── docs/                        # Website source (agentskills.io)
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── data.json                # Generated catalog data
│   ├── mcp.json                 # MCP server metadata
│   └── collections/             # Generated per-pack HTML pages
├── scripts/                     # Catalog build and validation scripts
└── Makefile
```

---

## Usage

```bash
# Install dependencies
make install

# Generate docs/data.json and collection pages
make generate

# Generate + verify site
make test

# Start local server at http://localhost:8000
make serve
```

---

## How It Works

```
Skills repos (source)            Internal process            This repo (output)
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│ agentic-collections- │     │ Fetch skills repos    │     │ marketplace/        │
│ skills/              │────>│ Evaluate & score      │────>│ docs/ (website)     │
│   rh-sre/            │     │ Build catalog data    │     │ data.json           │
│   ocp-admin/         │     │ Generate website      │     │ mcp.json            │
│   ...                │     └──────────────────────┘     └─────────────────────┘
└─────────────────────┘

```

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

**Maintained by:** [Red Hat Ecosystem Engineering](https://github.com/RHEcosystemAppEng)
