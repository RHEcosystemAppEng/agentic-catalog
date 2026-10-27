# AI5 Contributor Onboarding Guide

Everything you need to bring a skill, plugin, or MCP server into the AI5 Marketplace. Copy-paste commands throughout; anything still in flight is marked ⚠️.

> **You keep and maintain your own repository.** You do not fork or PR into `agentic-plugins` — that repo is the AI5 team's reference implementation only. Your repo must follow the same structure (§1) and ship its own CI. This is the N-repos model: every team's skills/plugins/MCPs live in their own repo, not one shared one.

**Last verified: 2026-10-27.**

**Steps:**

0. [Prerequisites](#0-prerequisites)
1. [Repo structure](#1-repo-structure)
2. [Choose or create a plugin](#2-choose-or-create-a-plugin)
3. [Compass manifests](#3-compass-manifests)
4. [Registering in Compass](#4-registering-in-compass)
5. [Marketplace evaluations](#5-marketplace-evaluations)
   - [5.1 Skill evaluation](#51-skill-evaluation)
   - [5.2 MCP evaluation](#52-mcp-evaluation)
6. [Push and what happens next](#6-push-and-what-happens-next)

## 0. Prerequisites

- Your own repo (GitHub or internal GitLab) — where everything below lives
- `uv`, `podman`, Python 3.11+ — for validation scripts and the mock MCP server
- **Red Hat VPN connected** — required to reach Compass and Konflux

## 1. Repo structure

Lay out your repository the same way `agentic-plugins` does internally — this is the structure the Compass manifests (§3) and evaluation pipeline (§5) expect to find:

```
your-repo/
├── catalog-info.yaml          # Compass root Location
├── system.yaml                # Compass System for your repo
├── <plugin>/
│   ├── catalog-info.yaml      # Location → plugin + skills
│   ├── <plugin>-plugin.yaml   # AiResource, type: plugin
│   ├── AGENTS.md               # required — persona, routing, MCP servers, global rules
│   ├── README.md
│   ├── mcps.json               # MCP servers this plugin wires up (if any)
│   ├── .catalog/                # generated marketplace metadata — hand-author, see below
│   └── skills/<skill-name>/
│       ├── SKILL.md
│       └── catalog-info.yaml   # AiResource, type: skill
├── mcps/
│   ├── <mcp-name>.yaml          # MCPServer manifest
│   └── <mcp-name>-schema.json   # mock-MCP schema, sibling of the manifest (§5.2)
└── submissions/<plugin>/<skill>/   # evaluation submission (§5.1)
```

What each piece is for:

- **`catalog-info.yaml` (root)** — Compass entry point for your whole repo; lists your `system.yaml` and every plugin's own `catalog-info.yaml`.
- **`system.yaml`** — the Compass System representing your repo as a whole; every plugin you add belongs to it.
- **`<plugin>/`** — one directory per plugin (§2 on what counts as a plugin). Its own `catalog-info.yaml` indexes the plugin's manifest and skills; `AGENTS.md` is required (persona, skill routing, MCP servers, global rules); `mcps.json` only if the plugin wires up MCP servers.
- **`.catalog/`** — the one *generated* directory in this tree; everything else is hand-authored and is the source of truth. In `agentic-plugins` itself it's regenerated from `SKILL.md`/`AGENTS.md`/`README.md` by a Claude Code skill; that tooling isn't available outside that repo yet, so write `.catalog/collection.yaml` by hand following [`COLLECTION_SPEC.md`](https://github.com/RHEcosystemAppEng/agentic-plugins/blob/main/COLLECTION_SPEC.md) — it needs `maturity: ORANGE` (until evaluated, then `GREEN`) and a roster entry per skill. `agentic-catalog` clones your repo and reads this file directly to build the public listing, so a missing or malformed one means your plugin silently never appears there.
- **`mcps/`** — one manifest (`<name>.yaml`) and one mock schema (`<name>-schema.json`, §5.2) per MCP server used anywhere in your repo.
- **`submissions/<plugin>/<skill>/`** — the evaluation submission for each skill (§5.1).

## 2. Choose or create a plugin

Decide whether your skill belongs in a plugin you already maintain or needs a new one — there's no central registry forcing either choice. A plugin can live in its own repository, entirely independent of any other plugin's. There's no limit on how many plugins exist or what they're for.

`agentic-plugins` groups its own plugins by persona/use case (`rh-sre`, `ocp-admin`, etc.) because that grouping works for the skills the AI5 team maintains — it's a convention that happens to fit us, not a requirement. Organize your own plugin(s) however makes sense for your team.

For the `SKILL.md` format itself, [`SKILL_DESIGN_PRINCIPLES.md`](https://github.com/RHEcosystemAppEng/agentic-plugins/blob/main/SKILL_DESIGN_PRINCIPLES.md) documents what AI5 considers good practice (structure, frontmatter fields, length) — worth reading, not mandatory to follow line-for-line. Real example: [`cluster-creator`](https://github.com/RHEcosystemAppEng/agentic-plugins/blob/main/ocp-admin/skills/cluster-creator/SKILL.md).

## 3. Compass manifests

**Use your own namespace and owner group** (e.g. namespace `<your-team>`, owner `group:redhat/<your-team>`) — confirmed with the Compass team. Don't copy `ai5-marketplace` from the examples below; that value is specific to `agentic-plugins`' own entities, not a shared namespace for every repo.

Four manifest kinds, all under `apiVersion: backstage.io/v1alpha1` except `MCPServer`:

- **`Location`** — an index pointing at other manifest files. Your root `catalog-info.yaml` and each plugin's own `catalog-info.yaml` are both this kind.
- **`System`** — represents your repo as a whole (`system.yaml`).
- **`AiResource`** — the actual entities: skills (`spec.type: skill`) and plugins (`spec.type: plugin`).
- **`MCPServer`** (`apiVersion: mcp/v1beta1`) — describes an MCP server's tools and how to run it.

**Skill** (`<plugin>/skills/<skill-name>/catalog-info.yaml`):

```yaml
apiVersion: backstage.io/v1alpha1
kind: AiResource
metadata:
  name: <skill-name>
  namespace: <your-namespace>
  title: <Skill Title>
  labels: {distribution: external}
  annotations:
    backstage.io/source-location: url:https://github.com/<org>/<repo>/blob/main/<plugin>/skills/<skill-name>/SKILL.md
spec:
  type: skill
  lifecycle: beta
  owner: group:redhat/<your-team>
  agents: []   # ALWAYS empty — Lola/Agent Plugin Spec handles compatibility, never enumerate
  dependsOn:
    - airesource:<namespace>/<plugin-name>
    - mcpserver:<namespace>/<server-name>   # one per MCP used
```

**Plugin** (`<plugin>/<plugin>-plugin.yaml`):

```yaml
apiVersion: backstage.io/v1alpha1
kind: AiResource
metadata:
  name: <plugin-name>
  namespace: <your-namespace>
  title: <Plugin Title>
  labels: {distribution: external}
spec:
  type: plugin
  lifecycle: beta
  owner: group:redhat/<your-team>
  system: default/<your-system-name>   # this alone links the plugin to your System
  agents: []
  dependencyOf:
    - airesource:<namespace>/<skill-name>   # one per skill in this plugin
  # do NOT also add `dependsOn: [system:...]` here, or `dependencyOf` back on system.yaml —
  # spec.system already generates that relationship; declaring it again is redundant.
```

**MCP server** (`mcps/<server-name>.yaml`):

```yaml
apiVersion: mcp/v1beta1
kind: MCPServer
metadata:
  name: <server-name>
  namespace: <your-namespace>
  title: <Human Title>
spec:
  type: local   # or "remote"
  lifecycle: beta
  owner: group:redhat/<your-team>
  system: default/<your-system-name>
  primitives:
    - type: tool
      name: <tool_name>
      description: <what this tool does>   # one entry per tool exposed
  dependencyOf:
    - airesource:<namespace>/<skill-name>   # every skill/plugin that depends on it
```

Everywhere except plugin↔system, relationships are manual and bidirectional (Compass doesn't auto-generate the inverse for custom kinds — **[COMPASS-1288](https://redhat.atlassian.net/browse/COMPASS-1288)**): a skill's `dependsOn` needs a matching `dependencyOf` on the plugin or MCP server it points to, and the skill's own `catalog-info.yaml` needs to be added as a target in the plugin's `Location`.

## 4. Registering in Compass

Authoring the manifests above doesn't register anything by itself — something still has to tell Compass to fetch and ingest your root `catalog-info.yaml`.

**How it works:** an AI5 team member submits the URL of your root `catalog-info.yaml` to Compass, registering it as a `Location`. **This only needs to happen once**, when the plugin is first registered. After that, Compass automatically re-scans the Location on its own refresh cycle (roughly every 2 hours) and picks up any changes you push — new skills, updated fields, new relationships — with no need to register again. If your repo is already registered, don't repeat these steps — just push your new/updated entities and wait for the next refresh cycle.

Registration steps (performed today by an AI5 team member on your behalf):

1. Go to Compass. We currently use **staging** — `https://compass.stage.redhat.com` — not production (`https://compass.redhat.com`), until we say otherwise. Both require Red Hat VPN and SSO.
2. Log in with SSO.
3. Left-side menu → **Self-service** → **Register an Entity** → paste the URL of the repo's root Location file → **Analyze** → check that every entity you expect shows up correctly.
4. Review and finish.

**To confirm it actually worked:** search for your plugin and skill names in the Compass catalog search and open each entity's page — confirm it exists, and that the `dependsOn`/`dependencyOf` relationships you declared (§3) show up correctly on both sides.

> ⚠️ **Manual today, not self-service for contributors.** A contributor can't trigger this themselves yet — it's done by an AI5 team member. **[APPENG-6233](https://redhat.atlassian.net/browse/APPENG-6233)** is designing a more scalable version of this; nothing is decided or built yet.

Reach out via the channel in Contacts once §3 is done to get your repo registered for the first time.

## 5. Marketplace evaluations

> ⚠️ **In progress — not yet 100% ready for other repos to plug into.** What's confirmed today: both skill and MCP evaluation run on **Konflux + Tekton**, on **internal Red Hat servers behind the VPN**, and every run automatically produces audit/security artifacts — **SBOM files** and **attestations** — alongside the evaluation result. The tasks that implement these pipelines live in [`RHEcosystemAppEng/konflux-ai5-evaluation`](https://github.com/RHEcosystemAppEng/konflux-ai5-evaluation). Ask in Contacts before depending on any of this for a real submission.

### 5.1 Skill evaluation

This is what the LLM-based evaluation stage actually runs against: a self-contained description, at `submissions/<plugin>/<skill-name>/` in your own repo, of how to exercise your skill and judge the result.

The core of it is `cases/`, holding as many `case-NNN/` test cases as you need — there's no fixed number, and **defining them is the skill owner's responsibility**, not something AI5 does for you. Cover the golden path, the error conditions you expect users to hit, and realistic edge cases; more cases means better coverage, and you can always add more later as gaps show up.

Real example in our own `agentic-plugins` repo: [`submissions/rh-sre/cve-impact/`](https://github.com/RHEcosystemAppEng/agentic-plugins/tree/main/submissions/rh-sre/cve-impact).

- `metadata.yaml` — `eval_engine: aeh`, `gate_policy` (gates + `push_facts` pointing at your skill's `entity_ref`).
- `eval.yaml` — `execution.skill` + `execution.arguments: "{{ input.prompt }}"` (required, or the prompt never reaches the agent), `runner.type: claude-code`, judges.
- `cases/case-NNN/` — one directory per test case: `input.yaml` is the prompt that should trigger the skill, `annotations.yaml` is the expected behavior to grade the response against.

### 5.2 MCP evaluation

**Skip this section if your skill doesn't use any MCP server** — not every skill needs one, and if yours doesn't, there's nothing here for you to do.

If your skill does use an MCP, evaluation needs it **mocked**, not called for real. This buys three things: it isolates MCP problems from skill problems (a flaky or unreachable MCP shouldn't fail your skill's evaluation, and vice versa), it gives every test case a deterministic, repeatable response instead of whatever live data happens to exist at run time, and it avoids the eval pipeline actually performing real actions against whatever the MCP talks to (e.g. actually creating a cluster, not just checking the skill asked for one correctly).

Two things to prepare: a **schema** (the MCP's tools and their contracts, so the mock knows what to emulate) and **fixtures** (the specific responses each test case expects).

**Schema** lives at `mcps/<mcp-name>-schema.json` in **your own repo** (not in `generic-mock-mcp-server` — that repo is engine code only). Generate it, don't hand-write it:

```bash
git clone git@github.com:RHEcosystemAppEng/generic-mock-mcp-server.git
cd generic-mock-mcp-server
python scripts/extract_mcp_schema.py --url http://127.0.0.1:8080/mcp --output /path/to/your-repo/mcps/<mcp-name>-schema.json
```

> ⚠️ This script needs the real MCP server **already deployed and running** — it extracts the schema by querying the live server's `tools/list`, it cannot generate one from source code alone.

`outputSchema`/`outputExample` aren't populated by the script (MCP has no concept of an example response) — fill those by hand per [SCHEMA.md](https://github.com/RHEcosystemAppEng/generic-mock-mcp-server/blob/main/SCHEMA.md).

**Fixtures** are the predefined responses the mock returns for a given test case, matching whatever flow that case exercises — per test case, not shared per MCP: `submissions/.../cases/case-NNN/fixtures/<mcp-name>.json`. Different cases can mock different MCP behavior (happy path vs. error) without conflict.

> ⚠️ Still open: today's pipeline only wires mocks for `lightspeed-mcp` and `openshift-mcp-server`, and deploys one mock per MCP for the whole run, not per case — the per-case fixtures layout above is the target design, not yet built. Ask (see Contacts) before depending on it for a real submission.

## 6. Push and what happens next

Commit to your own repo, your own workflow. Compass registration (§4) is separate from, and doesn't by itself trigger, automated evaluation — **how your repo gets wired into the Konflux evaluation pipeline is not yet defined** (**[APPENG-6233](https://redhat.atlassian.net/browse/APPENG-6233)**) — likely a `repository`/`path`/`ref` entry in `agentic-catalog`'s marketplace YAML plus a Konflux `Component`, but unconfirmed. Ask (see Contacts) before assuming a push triggers anything automatically.

Once wired in, expect (per `agentic-plugins`' own pipeline): Tier 1/2 lint + security scan + cheap evaluation checks on every PR (hard-fail on error); the expensive LLM-based evaluation only runs after merge, and only if the merge carried an `evaluate` label.

## Open items — ask before assuming

1. Compass registration is confirmed manual (§4) — a scalable/self-service design is still pending (**[APPENG-6233](https://redhat.atlassian.net/browse/APPENG-6233)**).
2. How an external repo gets wired into the Konflux evaluation pipeline to trigger automatically (**[APPENG-6233](https://redhat.atlassian.net/browse/APPENG-6233)**).
3. CI validation enforcement mechanism for external repos — in progress.
4. Per-case MCP mock fixtures (§5.2) — design only, not built.
5. Konflux token cost of per-case mock deployment, if/when built.
6. Lola's native OCI/plugin install support — in flux upstream; check the current state before documenting a specific command.

## Contacts

Slack channels:

- **`#forum-ai5-marketplace-onboarding`** — questions about any step in this guide: plugins, skills, MCPs, evaluation, or publishing.
- **`#forum-compass`** — Compass-specific questions (manifests, registration, the Compass Assistant).

Compass also has its own MCP server (**[UIEINFRA-841](https://redhat.atlassian.net/browse/UIEINFRA-841)**), powering the in-app Compass Assistant — it can answer questions about entities, relationships, and scorecards directly. Ask in `#forum-compass` for current setup/connection details.

| Area | Contact |
|---|---|
| AI5 Marketplace — plugins, skills, MCPs, evaluation, publishing | Alejandro Villegas (avillega@redhat.com), Shimon Tanny (stanny@redhat.com) |
| Compass — manifests, namespaces, registration | Mayur Deshmukh (mdeshmuk@redhat.com) |

## Useful links

- [Compass — Get Started](https://compass.redhat.com/docs/compass/system/compass-platform/get-started/)
