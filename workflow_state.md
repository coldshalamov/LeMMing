# Workflow State

## Current Task
Perform Step 1 analysis: scan existing `lemming/` modules to map current logic against the new resume-driven, pull-based architecture.

## Plan (3-7 steps)
- [x] Catalog current agent configuration sources (resume files, org chart, credits) and how they are loaded.
- [x] Trace messaging flow and file layout for outboxes/inboxes, noting any push-based assumptions.
- [x] Review scheduler/engine mechanics (loops, speed multipliers) and how ticks/turns are handled today.
- [x] Identify dependencies on role-specific logic or org chart structures that must be removed or generalized.
- [x] Summarize findings and gaps relative to mandates in this file for next implementation steps.

## Findings (Step 1 Analysis)
- **Resume/config sources**: `agents.py` loads agents from `agents/<name>/resume.txt` via `validate_resume_file`, extracting header fields plus `[INSTRUCTIONS]` and `[CONFIG]` JSON. Config requires `model`, `org_speed_multiplier`, `send_to`, `read_from`, and `max_credits`, and tools are optional keys passed through. Org relationships and credits are duplicated in `lemming/config/org_chart.json` and `credits.json`. 【F:lemming/agents.py†L25-L56】【F:lemming/config_validation.py†L17-L117】
- **Messaging path**: Messages are addressed to `agents/<sender>/outbox/<receiver>/msg_*.json`, requiring org-chart permission checks before write. Receivers poll other agents’ receiver-specific subfolders; processing moves files into `processed/`. Expiration cleanup traverses per-receiver folders. This is push-based and not aligned with the single outbox requirement. 【F:lemming/messaging.py†L17-L83】【F:lemming/file_dispatcher.py†L10-L32】
- **Scheduler/turns**: Engine uses `org_speed_multiplier` to decide if an agent runs on a given turn and can force manager summaries based on `org_config`. Execution loops forever with `base_turn_seconds`, lacking tick-based `(tick % run_every_n_ticks) == phase_offset` logic. 【F:lemming/engine.py†L49-L137】【F:lemming/engine.py†L165-L207】
- **Role/org dependencies**: Org permissions, credit limits, and send/read lists are centralized in `org_chart.json` and `credits.json`, cached via `org.py`. Engine forces manager-specific behavior (summary runs) and uses org chart for send/read validation, so the system is not generic or resume-driven. 【F:lemming/org.py†L14-L83】【F:lemming/engine.py†L165-L189】

## Repo Summary
- Filesystem-first multi-agent framework with CLI, FastAPI server, and dashboard; agents communicate via outboxes with org-chart permissions and credit tracking. Resumes currently use `resume.txt` with `[INSTRUCTIONS]` plus `[CONFIG]` JSON including `model`, `org_speed_multiplier`, `send_to`, `read_from`, and `max_credits` fields.
- Key Python modules live under `lemming/` (CLI, engine, messaging, org, memory, tools, model providers, API, config validation). Messaging/engine/org components support turn-based execution with credit use and outbox handling.
- `tests/` contains unit coverage for agents, config validation, engine, file dispatch, memory, messaging, models, org, and tools, indicating an established test suite.
- `agents/` includes default roles (`manager`, `planner`, `hr`, `coder_01`, `janitor`, `preference_memory`) plus `agent_template`, each with resume/outbox/memory folders following the current resume.txt schema.
- UI assets under `ui/` provide dashboard HTML pages; docs include README and a roadmap outlining future phases and features beyond the current version.

## Open Questions
- None yet; will note any uncertainties after the repository scan.

## Relevant Paths
- project root
- `logs/`
- `README.md`, `ROADMAP.md`
- `lemming/` package, `tests/`, `agents/`, `ui/`
