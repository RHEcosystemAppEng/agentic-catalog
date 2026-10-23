---
name: red-hat-security-mcp-setup
description: Add the Red Hat Security MCP server at the project or user level for the current tool. Configures stdio transport via npx mcp-remote and explains the Red Hat Customer Portal SSO browser login flow.
license: Apache-2.0
user_invocable: true
model: inherit
color: blue
allowed-tools:
---

# Red Hat Security MCP Setup

Add the Red Hat Security MCP server to the current tool's MCP configuration,
at either the project or user level.

## Prerequisites

- A Red Hat account at [console.redhat.com](https://console.redhat.com).
- Node.js with `npx` on PATH (the server is launched as
  `npx -y mcp-remote https://security-mcp.api.redhat.com/mcp`).

## When to Use This Skill

When the user wants to add the Red Hat Security MCP server to their project to enable live CVE and advisory lookups.

## Workflow

1. Ask the user whether to install at the **project level** (this workspace
   only) or the **user level** (every workspace opened with the current tool).
2. Detect the current agentic tool and resolve the target config file for
   the chosen level.
3. Locate the source `red-hat-security` entry: prefer this plugin's
   vendor-specific `com.<vendor>/mcp.json`, falling back to the plugin-root
   `mcp.json`, then to the inline skeleton.
4. Merge that entry into the target file without removing existing servers.
5. Explain the browser SSO authentication flow to the user.

## Dependencies

- Write access to the target MCP configuration file (project- or
  user-level, per the user's choice in Step 1).
- Read access to this plugin's directory, to locate `com.<vendor>/mcp.json`.

## Step 1 — Ask the user where to install

Ask the user to choose one:

- **Project-level** — only the current workspace gets the server.
- **User-level** — every workspace opened with the current tool gets the
  server.

For **Codex**, project-level `.mcp.json` is not loaded. Use the user-level
`~/.codex/config.toml` target (or rely on the plugin's own `mcp.json` after
install). If the user asks for project-level on Codex, explain that and use
the Codex user-level file instead.

## Step 2 — Detect the current tool and resolve the target file

Determine which agentic tool is currently executing this skill, then
resolve `$MCP_FILE` from the table below using the level chosen in Step 1.
`$PLUGIN_ROOT` is this plugin's install directory (the parent of this
skill's `skills/` folder).

| Current tool | Vendor namespace dir | Project-level target | User-level target |
|---|---|---|---|
| Claude Code | `com.anthropic.claude-code` | `<project>/.mcp.json` | `~/.claude/.mcp.json` |
| Cursor | `com.cursor.editor` | `<project>/.cursor/mcp.json` | `~/.cursor/mcp.json` |
| Codex | `com.openai.codex` | *(not used — see Step 1)* | `~/.codex/config.toml` |
| Other / unknown | *(plugin root)* | `<project>/.mcp.json` | `~/.mcp.json` |

```
PROJ=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
```

If the current tool isn't in the table, use the "Other / unknown" row and
tell the user the target location is a best-effort default they should
verify for their tool.

## Step 3 — Locate the source server config

Look for the `red-hat-security` entry to merge, in this order:

1. `$PLUGIN_ROOT/com.<vendor>/mcp.json` — the namespace dir for the
   currently executing tool (e.g. `./com.cursor.editor/mcp.json`,
   `./com.anthropic.claude-code/mcp.json`).
2. `$PLUGIN_ROOT/mcp.json` — the plugin-root fallback.
3. If neither file exists, use this skeleton:

```json
{
  "mcpServers": {
    "red-hat-security": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://security-mcp.api.redhat.com/mcp"]
    }
  }
}
```

Treat whichever source is found as read-only reference material — do not
edit it in place.

## Step 4 — Merge the entry into the target file

**JSON targets** (Claude, Cursor, unknown): if `$MCP_FILE` exists, read it
and merge in the `red-hat-security` stdio entry found in Step 3, without
removing any other servers already present. If it does not exist, create it,
wrapping the entry in `{"mcpServers": {...}}`. If an older HTTP /
`streamable-http` `red-hat-security` entry is present, replace it with the
stdio `npx` / `mcp-remote` entry.

**Codex `~/.codex/config.toml`:** merge a TOML table (not JSON). If
`[mcp_servers.red-hat-security]` exists, replace it. Append:

```toml
[mcp_servers.red-hat-security]
command = "npx"
args = ["-y", "mcp-remote", "https://security-mcp.api.redhat.com/mcp"]
```

Do not set `enabled = false`. Do not add headers, env, or tokens. If a
user-level Codex server with the same name would shadow the plugin MCP,
keep this stdio block and tell the user to restart Codex (including the
app-server daemon) so only one `red-hat-security` is active.

Write the result back to `$MCP_FILE`.

## Step 5 — Explain authentication to the user

Tell the user:

```
Red Hat Security MCP server added (stdio via npx mcp-remote).

Prerequisite: Node.js with npx on PATH.

Authentication: Red Hat Customer Portal SSO

The first time any tool from this server is called, a browser window will
open automatically so you can log in with your Red Hat account. After you
complete login, the session token is stored and subsequent calls proceed
without prompting.

If the browser does not open automatically, look for an authentication URL
printed in the MCP server output and open it manually.

Restart the agentic tool (or reload MCP servers) for the new configuration
to take effect. On Codex, quit the TUI and ensure the app-server daemon
restarts if /mcp still shows the old HTTP server.
```

## Notes

- This server exposes Red Hat security data (CVEs, advisories, errata). It
  is the backend used by `/red-hat-cve-explainer` when `get_cve_by_id` and
  related tools are available.
- An active Red Hat subscription is required to access the full dataset.
- Do not add `headers` or `env` auth fields to the target MCP config --
  `mcp-remote` handles authentication via the browser SSO flow.
- The table in Step 2 covers the tools this plugin ships instructions for.
  If a tool's exact config path is unconfirmed, say so explicitly instead
  of guessing silently.

