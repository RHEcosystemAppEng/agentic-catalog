# Documentation Site

GitHub Pages site for agentic-catalog. Generated from **this hub checkout** (`marketplace/`, `plugins/redhat/`, `claude-marketplace/`).

## Files

- [`index.html`](index.html) - Catalog home (Lola install uses `main` raw marketplace URL)
- [`styles.css`](styles.css) - Red Hat-themed styling
- [`app.js`](app.js) - Rendering and search (XSS-safe; no ZIP badges)
- `data.json` - Generated pack + MCP + Soundcheck + install metadata
- [`mcp.json`](mcp.json) - Hand-maintained MCP titles/tools merged onto servers parsed from hub `mcp.json`
- `.nojekyll` - Disables Jekyll processing

## Local Development

From the repository root:

```bash
make generate
make serve
```

Then visit: http://localhost:8000

Regenerate after changing packs, marketplace YAML, or scripts. Do not edit `data.json` or `collections/*.html` by hand.

## Data Generation

```bash
python ../scripts/build_website.py
```

Inputs:

- `marketplace/rh-agentic-collection.yml` — discovery, `ref`, Soundcheck, MCP scorecards
- `plugins/redhat/<pack>/` — `skills/`, `README.md`, `mcp.json`
- `claude-marketplace/marketplace.json` — Claude install metadata
- `docs/mcp.json` — optional titles/tools overlay by **mcp.json server key** (not Compass `mcp_evaluations[].name`)

There is **no** generate-time `git clone` and **no** ABEval `eval/` input. Packs whose marketplace `path` is not on disk are omitted.

### Soundcheck (marketplace YAML)

Pack cards use `evaluation_source: soundcheck`:

- Skill-track totals from `soundcheck_levels_summary` (pass/fail/total per level)
- Separate list `mcp_evaluations[]` keyed by Compass name / `entity_ref`

Do not treat `recommendation: pass` as a badge (pipeline constant). Do not overlay MCP evals onto `mcp.json` keys in this epic.

### Regenerating `mcp.json` enrichment

After hub `mcp.json` parse works, keep [`mcp.json`](mcp.json) keys aligned with pack server names (`lightspeed-mcp`, `openshift-self-managed`, …). Add a new key when a pack introduces a new server; omit keys that no published pack uses.

## Validation

```bash
make test
```

CI: `validate.yml` on PRs and on push to `main` / `rc/v1.0.0`. Pages deploy only from **`main`**.

## Security

All DOM manipulation in `app.js` uses `textContent` and `createElement`. No `innerHTML` with user-provided data.
