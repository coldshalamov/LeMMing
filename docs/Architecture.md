# Architecture

This document explains how the engine works under the hood while staying readable to operators. Everything revolves around files on disk and a deterministic tick loop.

## Filesystem layout
```
LeMMing/
├── agents/                # One folder per agent (canonical name from resume.json)
│   └── <agent>/
│       ├── resume.json    # Contract: identity, permissions, schedule, model
│       ├── resume.txt     # Optional instructions for humans/future UIs
│       ├── outbox/        # JSON messages produced by this agent
│       ├── memory/        # Durable key/value JSON entries
│       ├── logs/          # Activity logs per tick
│       └── workspace/     # Files agent may read/write (if permitted)
├── lemming/config/        # org_config.json, credits.json, models.json, derived org graph
├── logs/                  # Engine-level logs
├── ui/                    # Dashboard assets
└── tests/                 # Contract tests
```

## Agent lifecycle per tick
```mermaid
flowchart TD
    A[Load tick counter] --> B[Discover agents]
    B --> C[Validate resumes]
    C --> D[Compute schedule and fire list]
    D --> E[Build prompt (system preamble + resume instructions + memory + readable outboxes)]
    E --> F[Call model provider]
    F --> G[Parse JSON contract]
    G --> H[Write outbox entries]
    G --> I[Execute tool calls]
    G --> J[Apply memory updates]
    G --> K[Log notes + deduct credits]
    K --> L[Cleanup old outbox entries]
    L --> M[Persist next tick]
```

1. **Discover & validate** – The engine scans `agents/` (skipping the `agent_template`). Each `resume.json` is loaded; missing required fields or invalid types mark the agent invalid and it is skipped safely with a warning. The engine never crashes because of a bad resume.
2. **Schedule** – For each valid agent, compute whether it fires: `(tick + (phase_offset % N)) % N == 0` where `N = run_every_n_ticks`. Agents that fire are sorted deterministically by `(fire_point, agent_name)` where `fire_point = ((-phase_offset % N) / N)`.
3. **Prompt build** – The prompt includes the system preamble, the agent’s title and instructions, recent memory (`agents/<name>/memory/*.json`), and readable outbox context assembled from `permissions.read_outboxes`.
4. **Model call** – The configured provider is called via `model.key`. Credits are checked first; if `credits_left` is zero the agent is skipped.
5. **Parse JSON contract** – The engine expects a JSON object with `outbox_entries`, `tool_calls`, `memory_updates`, and `notes`. Unknown fields are ignored; missing fields default to empty lists/strings. Contract violations are logged and the tick continues.
6. **Apply actions** –
   - `outbox_entries` are written to `agents/<name>/outbox/<tick>_<uuid>.json`. Send permissions are enforced if `permissions.send_outboxes` is present.
   - `tool_calls` are executed only if the tool is allowlisted. File tools enforce normalized path allowlists from `permissions.file_access`.
   - `memory_updates` write or delete files under `agents/<name>/memory/`.
   - Credits are deducted per action and saved back to `lemming/config/credits.json`.
7. **Cleanup & logging** – Old outbox entries older than `max_outbox_age_ticks` (default 100) are removed. Engine logs are written under `logs/` and per-agent notes go to `agents/<name>/logs/activity.log`.

## Engine ↔ agent JSON contract
The model response must be valid JSON following this shape (fields optional but must exist):
```json
{
  "outbox_entries": [
    {"kind": "message", "payload": {"text": "..."}, "tags": ["optional"], "recipients": ["agent_a"]}
  ],
  "tool_calls": [
    {"tool": "file_write", "args": {"path": "workspace/note.md", "content": "hello"}}
  ],
  "memory_updates": [
    {"key": "status", "value": {"done": true}, "op": "write"}
  ],
  "notes": "Optional free-form string"
}
```

The engine ignores unknown keys and logs contract violations without stopping the tick.

## Validation rules
- Required resume fields: `name`, `title`, `short_description`, `model`, `permissions`, `schedule`, `instructions`.
- `permissions.read_outboxes` and `permissions.tools` must be lists; `permissions.send_outboxes` and `permissions.file_access` (if present) must be structured correctly.
- `schedule.run_every_n_ticks` > 0 and `schedule.phase_offset` is an integer.
- If a resume is invalid, that agent is skipped for the tick and the rest of the org proceeds.

## Identity rule
The canonical agent name is `resume.json.name`. The folder name is a convenience for humans; mismatches are logged. Duplicate canonical names are skipped to avoid ambiguity.

## Org graph derivation
The org chart is computed, not stored. `permissions.read_outboxes` defines who can see whose outbox. A derived graph file can be produced via `python -m lemming.cli inspect <agent>` or org helpers; it simply reflects these permissions. There is no global `org_chart.json` to keep in sync.
