# plan.md

## OVERVIEW
- **Purpose:** LeMMing is a filesystem-first multi-agent engine where each agent is defined solely by `agents/<name>/resume.json`, communicates via JSON `OutboxEntry` files in its own `outbox/`, and runs on a deterministic tick scheduler. Core services: agent discovery, prompt assembly, LLM dispatch, tool execution, credit accounting, memory persistence, API/UI surfacing, and CLI control.
- **Invariants:** resume-as-ABI, outbox-only messaging, tick-based scheduling, permissions derived from resumes (no central org chart), and all state/config/logs as files.
- **Current maturity:** v0.3-ish — core engine, tooling, FastAPI + dashboard, and tests exist, but resume.txt fallback, permissive send logic, and config/memory/tool safety need hardening.

## GAP ANALYSIS
- **PROJECT_RULES.md alignment gaps:**
  - **Addressed:** resume ABI is now JSON-only with `permissions` limited to `read_outboxes` and `tools`; templates and schema were updated accordingly.【F:lemming/agents.py†L91-L149】【F:agents/agent_template/resume.json†L1-L23】【F:lemming/schemas/resume_schema.json†L1-L69】
  - **Addressed:** engine no longer blocks outbox entries based on sender allowlists and preserves `to` recipients for compatibility.【F:lemming/engine.py†L355-L401】
  - File tools are now sandboxed to workspace/shared with no per-agent overrides, but further validation/logging hardening is still needed.【F:lemming/tools.py†L53-L99】
  - Org/credits still cached from config files; while derived org graph exists, schema validation and bootstrap safeguards are light compared to “validate on load” mandate.【F:lemming/org.py†L17-L83】
- **ROADMAP.md divergence/staleness:**
  - Roadmap claims “No tests” but repository has extensive pytest suite, so doc is stale regarding quality baseline.【F:ROADMAP.md†L12-L21】【F:tests/test_engine_contract.py†L1-L25】
  - Phases mention org-chart permissions and human agent CLI features that are only partially present (no human-in-loop CLI yet; org graph is derived but documentation still references outdated gaps).【F:ROADMAP.md†L29-L70】【F:lemming/api.py†L70-L116】
  - Dashboard phase expects real-time metrics; current API provides a websocket loop but Next.js UI is static and not wired for live data (needs reconciliation).【F:lemming/api.py†L147-L204】【F:ui/README.md†L1-L60】
- **Other stale docs:** Architecture/troubleshooting docs still reference legacy `file_access` overrides; these need to be rewritten to reflect the sandbox default. Workflow state was refreshed to track the new contract.【F:workflow_state.md†L1-L34】

## PHASED IMPLEMENTATION PLAN

### Phase 1: Core engine & messaging & memory hardening (MUST-have)
- Lock resume ABI to JSON only: drop `resume.txt` loader and simplify permissions to mandated fields in `lemming/agents.py`; update validation and template accordingly.
- Enforce outbox-only messaging contract: ensure `lemming/engine.py` writes messages without sender-specified recipients unless allowed by resume-derived topology; align `OutboxEntry` schema and context formatting in `lemming/messages.py`.
- Tighten scheduler determinism: audit `compute_fire_point`/`should_run` ordering and document invariants in code comments and README.
- Memory safety: constrain memory/tool writes to agent directory and add guardrails in `lemming/memory.py` + `lemming/tools.py` (e.g., path allowlists, error handling).
- Bootstrap/config integrity: add or update config validation so `models.json`, `credits.json`, and `org_config.json` are checked on load in `lemming/org.py` and `lemming/models.py`.

### Phase 2: Tests, config validation, logging, and error-handling (MUST-have)
- Expand pytest coverage to new invariants: resume-json-only loader tests, outbox recipient enforcement, tool permission denial, memory bounds checks (`tests/` updates + fixtures).
- Add schema/validation helpers for resumes and configs; enforce in CLI/bootstrap paths.
- Harden logging: structured logs for engine/agents with context (tick, agent, action) and rotate/trim where needed in `lemming/logging_config.py`.
- Error resilience: ensure `_parse_llm_output` and tool execution never raise; return safe defaults and log contract violations.

### Phase 3: Human-in-the-loop CLI + richer agent UX (MUST-have, with NICE-to-have)
- Implement CLI commands for sending/reading messages as a “human” agent (create `agents/human/resume.json` template) in `lemming/cli.py`.
- NICE: interactive REPL for chatting with agents; message history filters (tick, tags) leveraging `lemming/messages.py` utilities.
- Enhance agent inspection commands to surface schedule, permissions, and recent memory.

### Phase 4: FastAPI API + real-time metrics + dashboards (MUST-have)
- Wire API to expose derived org graph, tick, and per-agent stats with resume-ABI fidelity in `lemming/api.py`.
- Connect Next.js dashboard to websocket/API for live updates; add cards for tick, agent status, outbox streams under `ui/app` and `ui/components`.
- Add API tests for new endpoints and websocket serialization.

### Phase 5: Provider expansion, tools, production deployment, docs (NICE-to-have)
- Broaden provider support (Claude/Ollama/Azure) via `lemming/providers` and `lemming/models.py` registry entries; add configuration examples.
- Tooling enhancements: safer file/shell tools, organization-safe defaults, and new utility tools registered in `lemming/tools.py` with permission gates.
- Deployment polish: docker-compose/k8s manifests updated for API+UI, health checks, and env-based config; write operator docs in `README.md`/`docs/`.

## NON-GOALS
- Introducing centralized databases or non-filesystem message buses.
- Restoring deprecated push-style outbox layouts or org-chart config files.
- Embedding hardcoded role hierarchies; communication remains permission-derived.
- Supporting legacy `resume.txt` once migration completes.

## RISKS / GOTCHAS
- Path traversal or workspace escape via tools if allowlists are mis-specified—must canonicalize and enforce in file/shell tools.
- LLM output drift causing silent drops; maintain strict logging in `_parse_llm_output` and consider test fixtures for malformed JSON.
- Credit accounting races if multiple processes mutate `credits.json`; may need atomic writes or locking.
- Dashboard/API divergence: ensure websocket payloads stay backward-compatible with UI expectations.
- Cleanup jobs (outbox/memory) could delete needed context if max-age settings are too aggressive; document defaults in config.
