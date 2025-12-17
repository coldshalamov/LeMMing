# LeMMing Source of Truth
Version: 0.2 (living)
Repo: C:\Users\User\Documents\GitHub\Telomere\LeMMing
Role: Canonical specification for completing LeMMing end-to-end (engine, agents, tools, memory, UI, tests, docs).

---

## 0) Thesis
LeMMing is a resume-driven, filesystem-first multi-agent orchestration engine built for transparency, determinism, and composability.

Core vibe:
- If it matters, it is a file. No hidden state.
- Agents are small, composable, and operate via the filesystem.
- Agents never write directly to each other; they publish to outboxes.
- A deterministic tick scheduler decides who runs.
- Truth lives in inspectable state: resumes, outboxes, memory, logs, tool results.

Win condition: A user can inspect the repo tree to learn who the agents are, what they are allowed to do, what happened, why, and what will happen next.

---

## 1) Non‑negotiable invariants
### 1.1 Filesystem-first
All meaningful state is persisted as files that can be inspected and diffed.

### 1.2 Resume ABI governs behavior
Each agent lives in `agents/<name>/` with a mandatory `resume.json` (machine-readable ABI) and optional instructions (`resume.txt`). The engine treats `resume.json` as authoritative.

### 1.3 Outbox-only messaging
Agents only write to their own `outbox/`. Others read them only if permissions allow. No direct cross-agent writes.

### 1.4 Deterministic tick scheduler
Global integer tick. Each tick:
- discover agents
- decide which should run
- run in deterministic order
- collect outputs
- execute tool calls (if allowed)
- persist memory updates
- append logs

### 1.5 Engine ↔ agent contract
Each agent run returns structured JSON with top-level keys:
- `outbox_entries`: list
- `tool_calls`: list
- `memory_updates`: list
- `notes`: string

Engine is tolerant to missing keys (defaults + logs a contract violation) but tests enforce compliance.

### 1.6 Permissions enforced
File read/write and tool allowlists are enforced before execution. Paths are canonicalized to prevent traversal.

---

## 2) Repository mental model of “done”
### Engine
- deterministic tick loop
- agent discovery
- context building (instructions + memory + virtual inbox)
- model invocation via provider abstraction
- contract parsing and validation
- tool dispatch with permission checks
- memory store updates
- logging/observability
- reproducibility (same inputs ⇒ same decisions)

### Agents
- each in `/agents/<name>/`
- required `resume.json`; optional `resume.txt`
- `outbox/`, optional `memory/`, `workspace/`, `logs/`
- optional per-agent tests

### Tools
- explicitly allowed per agent
- tool outputs written to disk
- tool errors structured and logged
- file tools defended against traversal
- “dangerous” tools require explicit permissions

### UI / Dashboard
- agents list with metadata (name, schedule, permissions, tools, model)
- derived permission graph (who reads whose outboxes)
- tick timeline (what ran, order, rationale)
- per-agent outbox entries
- memory diffs over time
- tool calls + results + errors
- search/filter; optional cost accounting

### Tests
- scheduler determinism
- contract parsing
- permission enforcement
- file canonicalization
- golden-run snapshot for small agent set
- integration test: run N ticks in a temp repo and assert outputs

### Docs
- how to add an agent
- how to write `resume.json`
- how permissions work
- how tools are invoked
- how to debug a tick
- how to run UI
- how to run tests

---

## 3) Recommended directory layout
- `/lemming/`            ← core engine code
- `/agents/`             ← agent folders
- `/lemming/tools/`      ← tool implementations + registry
- `/ui/`                 ← dashboard/app
- `/tests/`              ← unit + integration tests
- `/docs/`               ← docs (include whitepaper here)
- `/scripts/`            ← helpers (lint, run ticks, generate graphs)

Agent folder shape:
- `agents/<agent_name>/`
  - `resume.json`
  - `resume.txt` (optional)
  - `outbox/`
  - `memory/`
  - `workspace/`
  - `logs/`

---

## 4) Scheduling (determinism knobs)
A schedule is simple and cron-like:
- `run_every_n_ticks` (N > 0)
- `phase_offset` (integer; normalize by N)

Fire condition example:
- `should_run = (tick % N) == (phase_offset % N)` (or equivalent, but consistent)

Deterministic within-tick ordering: stable sort by `(computed fire_point, agent_name)` or equivalent.

---

## 5) Permissions and safety
### File access
Agent resume defines allowlists:
- `allow_read`: [path prefixes]
- `allow_write`: [path prefixes]

Before any tool reads/writes:
- resolve relative paths against repo root
- normalize `.`, `..`
- canonicalize symlinks where feasible
- enforce prefix allowlist match

### Tool allowlist
Agent resume defines allowed tools by name. Engine denies calls if not allowed. Tool calls should include tool name, args, intended file paths (if applicable), and optional rationale.

### Logging for safety
Denied actions are logged (structured). Nothing fails silently.

---

## 6) Context building for model input
Each agent run receives a prompt/context assembled from:
- engine contract + instructions
- agent resume instructions
- agent memory summary/state
- virtual inbox: recent outbox entries from permitted sources
- optional tool result summaries or recent logs (bounded)

Context must be intentionally compacted; prefer summarizing into memory files to avoid unbounded prompts.

---

## 7) Memory model
Memory lives as files per agent. Minimum viable:
- `memory/<key>.json`
- updates either overwrite a key or append to a log-style stream

Memory update shape:
- `key`
- `operation`: set | append | merge
- `value`
- `timestamp_utc`
- `tick`

---

## 8) Outbox entry schema (suggested)
JSON file, append-friendly:
```
{
  "timestamp_utc": "...",
  "tick": 123,
  "agent": "planner_agent",
  "kind": "status|fact|task|decision|artifact|error|tool_result",
  "payload": {...},
  "tags": ["scheduler", "ui", "tests"]
}
```

---

## 9) UI spec (debugger-first)
### Views
1) Overview: current tick, enabled agents, last N runs, errors/warnings
2) Agents: table (name, schedule, phase, last run, model, tools) → click detail
3) Agent detail: resume viewer, permissions viewer, outbox feed (filter), memory viewer (diff + snapshot), tool calls + results, logs
4) Tick timeline: list of ticks; per tick ordered run list; click run → input context summary + output JSON + tool results
5) Graph: derived `read_outboxes` graph; highlight selected agent; optionally show tool permissions per node
6) Search: global search across outboxes, logs, memory keys, tool results

### UX principles
- fast filter/search
- copy-friendly JSON panels
- explicit timestamps/ticks
- never hide errors
- everything linkable to a file path in the repo

---

## 10) Finish-line checklist
### Milestone A: Engine correctness
- deterministic scheduling
- contract parsing
- robust error handling
- minimal provider integration working

### Milestone B: Permissions + tools
- canonicalization
- allowlists
- deny logs + tests

### Milestone C: Example agents
- planner-like agent
- executor-like agent
- research agent (optional)
- UI summarizer agent (optional)
All with clean resumes and outbox entries.

### Milestone D: UI usable
- agent list
- run list
- outbox viewer
- memory viewer
- search
- graph

### Milestone E: Tests + docs
- unit tests for scheduler/permissions/contract
- integration test that runs ticks and asserts outputs
- docs that teach extension

---

## 11) Research refresh protocol
Agents are encouraged to periodically gather human evidence on:
- agentic coding workflows and context management
- multi-agent orchestration failure modes, evals, reliability techniques
- safety/sandboxing patterns
- determinism and reproducibility patterns
- UI patterns for observability dashboards

When they learn something actionable, they must write what they looked up, conclusions, and plan changes into a persistent repo note (e.g., `dev_bus/RESEARCH_NOTES.md`).

---

## 12) Evolution of this doc
This file is living. Agents may rewrite to clarify ambiguities, align with repo reality, or tighten definitions. It must stay canonical: the repo evolves to match it, and it evolves to reflect truth.
