# Agentic Collections Catalog

Unified marketplace and website for Red Hat agentic skill collections. This repository aggregates content from skills source repositories and publishes it through [Lola](https://github.com/LobsterTrap/lola) and [agentskills.io](https://agentskills.io).

**This is not a skills development repository.** Skills are authored in source repositories like [agentic-collections-skills](https://github.com/RHEcosystemAppEng/agentic-collections-skills). An internal process fetches, evaluates, and assembles the catalog automatically.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## Structure

```
agentic-collections-catalog/
├── marketplace/                 # Lola marketplace definition
│   └── rh-agentic-collection.yml
├── catalog/                     # Collection schema for .catalog/ validation
│   └── schema.yaml
├── docs/                        # Website source (agentskills.io)
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── data.json                # Generated catalog data
│   ├── plugins.json             # Plugin registry
│   ├── mcp.json                 # MCP server metadata
│   └── collections/             # Generated per-pack HTML pages
├── scripts/                     # Catalog build scripts
├── COLLECTION_SPEC.md           # Specification for .catalog/ structure
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
│   ocp-admin/         │     │ Generate website      │     │ plugins.json        │
│   ...                │     └──────────────────────┘     └─────────────────────┘
└─────────────────────┘
```

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

**Maintained by:** [Red Hat Ecosystem Engineering](https://github.com/RHEcosystemAppEng)
