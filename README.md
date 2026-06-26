# Agentic Collections Catalog

Marketplace and catalog for Red Hat agentic skill collections. This repository contains the [Lola](https://github.com/LobsterTrap/lola) marketplace configuration, collection metadata, and the website for [agentskills.io](https://agentskills.io).

## Structure

```
agentic-collections-catalog/
├── marketplace/                 # Lola marketplace definition
│   └── rh-agentic-collection.yml
├── catalog/                     # Collection schema
│   └── schema.yaml
├── docs/                        # Website (agentskills.io)
├── scripts/                     # Catalog build and validation scripts
├── COLLECTION_SPEC.md           # Collection specification
└── <pack-name>/
    └── .catalog/                # Per-pack catalog metadata
        ├── collection.yaml
        └── collection.json
```

## Packs

| Pack | Description |
|------|-------------|
| `rh-sre/` | Site Reliability Engineering |
| `ocp-admin/` | OpenShift Administration |
| `rh-virt/` | Virtualization Management |
| `rh-developer/` | Developer Tools |
| `rh-basic/` | Getting Started |
| `rh-ai-engineer/` | AI Engineering |
| `rh-automation/` | Automation & Ansible |

## License

Apache 2.0 - See [LICENSE](LICENSE).
