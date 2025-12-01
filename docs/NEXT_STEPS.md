# Next Steps for LeMMing

## Current Snapshot
- **Filesystem-first engine is present**: Turn loop, agent discovery, and messaging are implemented with outbox files and simple JSON configs.
- **Baseline agents and configs exist**: Manager/Planner/HR/Coder/Janitor plus a template and human placeholder; default org/chart/credits/models configs are in place.
- **CLI/API foundations**: CLI covers bootstrap/run/chat/status and the API server exists, though validation and ergonomics are light.
- **Memory and messaging are minimal**: File-backed memory helpers exist but lack patterns; resume parsing is permissive with few guardrails.
- **Tests provide coverage**: Core modules are exercised, but fixtures and validations are thin and allow silent misconfiguration.

## Proposed Work (Grouped Themes)
### 1) Agent Contract & Resume Format
- Harden resume parsing with explicit headers/sections, required keys, and actionable errors in `lemming/agents.py`.
- Introduce a small validation helper (e.g., `config_validation.py`) to check resume config types (`model`, `org_speed_multiplier`, `send_to`, `read_from`, `max_credits`).
- Document the expected resume layout in README and template comments so new agents start from a consistent contract.

### 2) Config Validation & Safety Nets
- Add schema-like validation for `org_chart.json`, `org_config.json`, `credits.json`, and `models.json`; surface clear errors during load in `org.py`/`models.py`.
- Provide a CLI command (`validate`) to run all config/resume checks and exit non-zero on failures for CI friendliness.
- Cache invalidation remains but should never mask load-time errors.

### 3) Memory Patterns & Reusable Helpers
- Extend `lemming/memory.py` with helpers for appending timestamped events, fetching recent entries, and summarizing short histories.
- Add an example memory-focused agent (e.g., `preference_memory`) showing how to capture user feedback/history using the helpers.
- Consider lightweight retention guidance (e.g., capping list lengths) to keep per-agent memory manageable.

### 4) CLI & Developer Ergonomics
- Improve help text/descriptions and consolidate messaging for bootstrap/run/inspect.
- Add `validate` and `inspect-config` style commands to surface org/credit/model status and validation results quickly.
- Keep command logic thin and reusable from library functions to simplify testing.

### 5) Docs & UX Alignment
- Update README/ROADMAP snippets to reflect current behavior (turn loop, validation, memory helpers, resume contract).
- Add brief inline comments in templates/configs to guide customization without hiding mechanics.
- Outline “agent builder” prerequisites (validated resume schema + config validation) to inform future UI work.

### 6) Example Orgs & Defaults
- Refresh default `agents/` configs to include a lightweight memory agent and ensure org chart/credits include it.
- Provide a short walkthrough (possibly in docs/) for spinning up a small org that logs user preferences or project history.

These tasks keep the framework file-backed and inspectable while tightening the contract between humans, agents, and the engine.
