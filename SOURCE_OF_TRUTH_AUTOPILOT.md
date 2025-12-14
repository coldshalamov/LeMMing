# LeMMing Source of Truth
Version: 0.1 (Living Document)
Repo root: C:\Users\User\Documents\GitHub\Telomere\LeMMing
Purpose: The canonical “north star” for completing LeMMing end-to-end (engine + agents + tools + memory + UI + tests + docs).
Tone: ambitious, practical, deterministic where it matters, exploratory where it helps.

---

## 0) What LeMMing *is* (the thesis)
LeMMing is a resume-driven, filesystem-first multi-agent orchestration engine built for transparency, predictability, and composition.

**Core vibe:**
- Every meaningful artifact is a file.
- Agents are small and composable, not one mega-agent.
- Agents do not directly message each other; they publish to outboxes.
- A deterministic tick scheduler decides who runs.
- “Truth” lives in inspectable state: resumes, outboxes, memory, logs, tool results.

**The win condition:**
A user can inspect the repo directory tree and understand:
- who the agents are,
- what they’re allowed to do,
- what they did,
- why they did it,
- what will happen next.

---

## 1) The non-negotiables (load-bearing invariants)
These are the invariants that make LeMMing not collapse into magical-thinking orchestration:

### 1.1 Filesystem-first truth
If it matters, it becomes a file. No hidden DB magic. No “trust me bro” state.

### 1.2 Resume ABI governs behavior
Each agent exists as a folder containing a `resume.json` (canonical machine ABI) and optional instructions (like `resume.txt`).
The engine must treat `resume.json` as authoritative.

### 1.3 Outbox-only messaging (no direct agent-to-agent writes)
Agents only write to their own outbox. Others read them only if permissions allow.

### 1.4 Tick scheduler (deterministic)
There is a global integer tick.
Each tick:
- discover agents
- decide which should run
- run them in deterministic order
- collect outputs
- execute tool calls (if allowed)
- persist memory updates
- append logs

### 1.5 Strict-ish contract between engine and agent
Every agent run returns structured JSON with these top-level keys:
- outbox_entries: list
- tool_calls: list
- memory_updates: list
- notes: string

The engine should be robust to missing keys (default + log contract violation), but tests should enforce compliance.

### 1.6 Permissions are real
File read/write allowlists and tool allowlists must be enforced before execution.
Paths must be canonicalized to avoid traversal/symlink shenanigans.

---

## 2) Repository mental model (what “complete” looks like)
LeMMing “done” means:

### Engine
- deterministic tick loop
- agent discovery
- context building (instructions + memory + virtual inbox)
- model invocation (provider abstraction)
- contract parsing and validation
- tool dispatch with permission checks
- memory store updates
- logging/observability
- reproducibility (same inputs → same decisions as much as possible)

### Agents
- each agent is a folder in `/agents/<name>/`
- each has resume.json
- each has an outbox/ folder
- optional memory/ folder
- optional workspace/ folder
- optional logs/ folder
- optional tests that validate behavior

### Tools
- tools are explicitly allowed per agent
- tool outputs are written to disk
- tool errors are structured and logged
- file tools are safe against traversal
- “dangerous” tools are behind explicit permissions

### UI / Dashboard
A UI that is useful for debugging:
- shows agents list with metadata (name, schedule, permissions, tools, model)
- shows derived permission graph (who reads whose outboxes)
- shows tick timeline (what ran, in what order, and why)
- shows per-agent outbox entries
- shows memory diffs over time
- shows tool calls + results + errors
- provides search/filter
- optionally shows “cost” accounting / credits/budget if implemented

### Tests
- scheduler determinism tests
- contract parsing tests
- permission enforcement tests
- file canonicalization tests
- “golden run” snapshot tests for a small set of agents
- integration test: run N ticks in a temp repo, verify outputs

### Docs
- “how to add an agent”
- “how to write a resume.json”
- “how permissions work”
- “how tools are invoked”
- “how to debug a tick”
- “how to run UI”
- “how to run tests”

---

## 3) Canonical directory layout (recommended)
These are strong recommendations; the repo can vary, but clarity matters.

- /engine or /lemming/          → core engine code
- /agents/                      → agent folders
- /tools/ or /lemming/tools/    → tool implementations + registry
- /ui/                          → dashboard/app
- /tests/                       → unit + integration tests
- /docs/                        → docs (include the whitepaper here too)
- /scripts/                     → helpers (lint, run ticks, generate graphs)

Each agent:
- agents/<agent_name>/
  - resume.json
  - resume.txt (optional)
  - outbox/
  - memory/
  - workspace/
  - logs/

---

## 4) Scheduling details (determinism knobs)
A schedule should be simple and cron-like:
- run_every_n_ticks (N > 0)
- phase_offset (integer; normalize by N)

Fire condition example:
- should_run = (tick % N) == (phase_offset % N)
(or equivalent normalized form; pick one and make it consistent)

Deterministic within-tick ordering:
- must be stable across OS/filesystem ordering
- recommended: sort by (computed fire_point, agent_name)

---

## 5) Permissions and safety model (be paranoid here)
### File access
Agent resume defines allowlists:
- allow_read: [path prefixes]
- allow_write: [path prefixes]

Before any tool reads/writes:
- resolve relative paths against repo root
- normalize ., .. 
- canonicalize symlinks where feasible
- enforce prefix allowlist match

### Tool allowlist
Agent resume defines allowed tools by name.
Engine denies tool call if not allowed.
Tool calls should include:
- tool name
- args
- intended file paths (if applicable)
- rationale (optional but nice)

### Logging for security
Denied actions should be logged (structured).
Do not silently ignore.

---

## 6) “Context building” (how the engine feeds the model)
Each agent run gets a prompt/context assembled from:
- engine contract and instructions
- agent resume instructions
- agent memory summary/state
- virtual inbox: recent outbox entries from permitted sources
- optionally: tool results summaries or recent logs (bounded)

Important: context should be compacted intentionally.
Prefer summarizing to memory files rather than infinite prompt growth.

---

## 7) Memory model
Memory lives as files per agent.
Minimum viable:
- memory/<key>.json
- updates either overwrite a key or append to a log-style memory stream

Memory updates should be structured:
- key
- operation: set/append/merge
- value
- timestamp/tick

---

## 8) Outbox entry schema (suggested)
Outbox entries should be inspectable and greppable. A solid default:

{
  "timestamp_utc": "...",
  "tick": 123,
  "agent": "planner_agent",
  "kind": "status|fact|task|decision|artifact|error|tool_result",
  "payload": {...},
  "tags": ["scheduler", "ui", "tests"]
}

---

## 9) UI spec (verbose and useful)
The UI should be a debugger for the whole organism.

### Pages / Views
1) Overview
- current tick
- which agents are enabled
- last N runs summary
- errors/warnings

2) Agents
- table: name, schedule, phase, last run, model, tools
- click agent → details

3) Agent detail
- resume.json viewer
- permissions viewer
- outbox feed (filter by kind/tag)
- memory viewer (diff + current snapshot)
- tool calls feed + results
- logs

4) Tick timeline
- list of ticks
- per tick: ordered run list
- click run → input context summary + output JSON + tool results

5) Graph view
- derived read_outboxes graph
- highlight selected agent’s inbound/outbound
- optionally show tool permissions per node

6) Search
- global search across outboxes, logs, memory keys, tool results

### UX principles
- fast filter/search
- copy-friendly JSON panels
- explicit timestamps/ticks
- never hide errors
- everything linkable to a file path in the repo

---

## 10) “Finish LeMMing” milestone checklist
This is the “ship it” list.

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
- a planner-like agent
- an executor-like agent
- a research agent (optional)
- a UI summarizer agent (optional)
All with resumes and clean outbox entries.

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

## 11) Research refresh (stay informed by human evidence)
The agents are allowed (encouraged) to periodically do web/MCP research, specifically:
- vibe coding best practices (agentic coding workflows, context management)
- multi-agent orchestration learnings (failure modes, evals, reliability techniques)
- safety and sandboxing patterns
- determinism and reproducibility patterns
- UI patterns for observability dashboards

The rule: when they learn something actionable, they must write:
- what they looked up
- what they concluded
- how it changes the plan
into a persistent repo note (e.g., docs/RESEARCH_JOURNAL.md or dev_bus/shared/RESEARCH_NOTES.md).

---

## 12) How this doc should evolve
This file is living. Agents can and should rewrite it:
- clarify ambiguities
- incorporate repo reality
- tighten definitions
- add diagrams
But it must remain the canonical spec: the repo evolves to match it, and it evolves to reflect truth.

END.
