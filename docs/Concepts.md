# Core Concepts

LeMMing is intentionally literal: every concept is a folder or file you can open. This section introduces the primitives in plain language with just enough structure to extend the engine safely.

## Agent = directory-backed worker persona
An agent lives under `agents/<folder>/`. The canonical identity is the `name` inside `resume.json`; the folder name is advisory. If a resume name clashes with another agent, the duplicate is skipped with a warning rather than crashing the engine.

A typical agent directory contains:
- `resume.json` — the contract and ID card.
- `outbox/` — messages this agent has produced.
- `memory/` — durable notes as JSON files.
- `logs/` — activity logs from engine runs.
- `workspace/` — files the agent can read/write if allowed.

## resume.json = ID card + permissions + schedule
`resume.json` is the ABI between the human operator and the engine. It declares:
- `name`, `title`, `short_description`, `workflow_description`
- `model` (provider key, temperature, max_tokens)
- `permissions` (read_outboxes, tools)
- `schedule` (run_every_n_ticks, phase_offset)
- optional `credits` caps

Example (annotated):
```jsonc
{
  "name": "planner",                // Canonical agent name
  "title": "Project Planner",       // Short title for UI
  "short_description": "Plans the next tasks",
  "workflow_description": "Look at upstream messages and break work into tasks",
  "instructions": "Summarize asks, draft tasks, and route them to teammates.",
  "model": { "key": "gpt-4.1-mini", "temperature": 0.2 },
  "permissions": {
    "read_outboxes": ["researcher"], // Virtual inbox
    "tools": ["memory_write", "file_write"]
  },
  "schedule": { "run_every_n_ticks": 2, "phase_offset": 1 },
  "credits": { "max_credits": 400, "soft_cap": 200 }
}
```

Agents rely on the `instructions` string inside `resume.json` as their “mind.” Long-form notes belong in `memory/` rather than in legacy `resume.txt` files.

## Outbox-only messaging
Agents never write into another agent’s folder. They return `outbox_entries` in the LLM JSON contract; the engine saves each entry into `agents/<name>/outbox/`. Other agents build a virtual inbox from the outboxes listed in their `permissions.read_outboxes` (or `*` for all).

Example outbox entry produced by an agent:
```json
{
  "kind": "message",
  "payload": {"text": "New draft ready at workspace/draft.md"},
  "tags": ["handoff", "draft"],
  "recipients": ["reviewer"],
  "meta": {"to": "reviewer"}
}
```

## Memory = durable notes stored on disk
Memory entries are simple JSON files under `agents/<name>/memory/` named `<key>.json`. Agents emit `memory_updates` in their JSON contract, or call the `memory_write`/`memory_read` tools directly. Each entry stores `{key, value, timestamp, agent}`.

Example memory update in the model output:
```json
{
  "key": "daily_snapshot",
  "value": {
    "date": "2024-06-01",
    "decisions": ["Ship UI copy"],
    "risks": ["Need API key"],
    "next_steps": ["Draft release note"]
  }
}
```

## Tools = capabilities guarded by allowlists
Tools are registered capabilities such as `file_read`, `file_write`, `file_list`, `shell`, `memory_read`, `memory_write`, `create_agent`, and `list_agents`. Agents may only invoke tools listed in `permissions.tools`. File tools are sandboxed to `agents/<name>/workspace/` plus `shared/` by default; there is no per-agent file allowlist surface in the resume.

Example tool call emitted by the model:
```json
{
  "tool": "file_write",
  "args": {"path": "workspace/plan.md", "content": "- [ ] Ship docs"}
}
```

## Credits = run budget
Credits live in `lemming/config/credits.json`. Each agent has a `credits_left` balance and `cost_per_action`. If an agent has no credits, the engine logs a skip and moves on; it does not crash. Credits can be topped up via the CLI (`python -m lemming.cli top-up <agent> 100`).

## Messaging model recap
- There is no inbox directory. The engine computes it dynamically from allowed outboxes.
- Unknown fields in a model response are ignored, and missing required fields fall back to defaults so that agents cannot break the tick.
- The canonical agent identity is the `resume.json.name`; folder names help humans but are not authoritative.

## Walk-through: manager → researcher → coder
1. **Tick 1:** `manager` fires (scheduled), reads no prior messages, and posts a task list to its outbox.
2. **Tick 2:** `researcher` fires, reads `manager`’s outbox, writes findings to its own outbox and `memory/research.json`.
3. **Tick 3:** `coder` fires, reads both outboxes, writes `workspace/feature.py` via `file_write`, and posts a status message.
4. **Tick 4:** `manager` fires again, reads the latest outboxes, and updates `memory/status.json` with merged progress.

By inspecting the folders after each tick you can reconstruct the entire conversation and decision trail.

## Department = logical grouping of agents

A department is a set of agents that work together towards a common goal. Department metadata lives in `departments/<name>.json`:

```jsonc
{
  "name": "content_team",           // Department identifier
  "description": "Content creation workflow",
  "version": "1.0.0",           // Semantic version
  "author": "Organization Name",   // Creator attribution
  "tags": ["content", "writing"],  // Categorization
  "dependencies": ["research"],     // Other departments needed
  "readme": "# Department docs\n..." // Detailed documentation
}
```

Departments enable:
- **Modularity**: Package and share groups of agents
- **Organization**: Structure large multi-agent systems
- **Social analysis**: Track relationships between departments
- **Emergent behavior**: Complex workflows from simple interactions

Use `python -m lemming.cli department-*` commands to manage departments.
