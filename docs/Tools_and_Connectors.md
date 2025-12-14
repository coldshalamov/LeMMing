# Tools and Connectors

Tools are how agents touch the world. In LeMMing, a connector is just a tool with a friendly name. The product layer can present them as a curated catalog, while the engine keeps a strict, permissioned interface.

## What counts as a tool
- Filesystem operations: `file_read`, `file_write`, `file_list`
- Shell execution: `shell` (scoped to the agent workspace)
- Memory operations: `memory_read`, `memory_write`
- Org utilities: `create_agent`, `list_agents`
- Future connectors: web fetchers, APIs, or external systems exposed through the same contract

Agents can only call tools listed in `permissions.tools` within `resume.json`. Unknown tool names result in a safe error recorded in the tool results.

## Tool permission model
- **Allowlists only:** No implicit access. If a tool is not listed, the engine will not execute it.
- **File access:** `permissions.file_access` declares `allow_read` and `allow_write` path prefixes. Paths are canonicalized (resolved) before checking; access is granted only when the canonical path is within an allowlisted prefix.
- **Send restrictions:** If `permissions.send_outboxes` is present, outgoing outbox entries must include recipients and must be within the allowlist.
- **Credits:** Even permitted tool calls only run when the agent has credits remaining.

### Path rules
1. Canonicalize first: resolve relative paths against `agents/<name>/workspace/`, resolve symlinks, normalize separators.
2. Prefix-match against each allowlisted path. If no prefix matches, deny.
3. Defaults: if `file_access` is missing, the engine defaults to `agents/<name>/workspace/` and `shared/` directories for read/write.

## Safe defaults and forward compatibility
- Unknown tool fields in `resume.json` or model responses are ignored by older engines but should be preserved by UIs so future engines can use them.
- Unknown message kinds or outbox fields must be kept intact in the timeline; viewers should display them instead of dropping fields.
- If a resume is missing required sections, the agent is skipped with a warning instead of crashing the engine.

## UI expectations
- A “Tool Store” panel lists available tools/connectors with friendly descriptions and permissions required.
- Per-agent toggles allow enabling/disabling tools; file access allowlists should be editable as readable paths.
- Configuration drawers for common connectors (API keys, base URLs) should write back to the agent’s configuration while keeping the canonical JSON contract intact.

## Example: enabling filesystem access
In `resume.json`:
```json
{
  "permissions": {
    "tools": ["file_read", "file_write", "file_list"],
    "file_access": {
      "allow_read": ["shared", "agents/researcher/workspace"],
      "allow_write": ["agents/researcher/workspace"]
    }
  }
}
```
The UI should surface these as checkboxes and editable paths, while the engine enforces canonicalization and prefix checks at runtime.
