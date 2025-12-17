## 2025-12-14 05:26 ET — bootstrap
- Created canonical spec `LEMMING_SOURCE_OF_TRUTH.md` in repo root (v0.2 living copy based on prior autopilot doc).
- Verified docs/ already contains whitepaper (`LeMMing_Whitepaper_v1.0.txt` and docx) and other specs.
- Created `dev_bus/` for lab notes and initialized this notebook.
- Next: map code/tests, run pytest baseline, audit engine/permissions/scheduler vs spec, and plan first fixes.

## 2025-12-14 05:30 ET — baseline tests
- Setup `.venv` and installed deps via `.venv\\Scripts\\python -m pip install -e .[dev,api,llm]`.
- Ran `.venv\\Scripts\\python -m pytest`: 17 failures / 20 passes.
- Failures clustered around missing default model key in AgentModel usage, scheduler fire_point helpers, CLI/API assuming valid agent resumes (instructions required), credits handling None in org._ensure_credit_entry, permissions default blocking workspace.
- Next focus: inspect `lemming/models.py`, `agents.py`, scheduler helpers, org credits, tools permissions to satisfy tests and spec invariants.

## 2025-12-14 05:40 ET — fixes + green tests
- Hardened agent dataclasses with sensible defaults: AgentModel/AgentSchedule/AgentPermissions/AgentCredits default values, workflow/instructions default strings, credits default factory, FileAccess list defaults.
- Relaxed resume validation to allow empty instruction strings and default model when absent; Agent.from_resume_data now supplies default credits when resume lacks them.
- Result: full suite green (`.venv\\Scripts\\python -m pytest` → 37/37 passed).
- Next: audit broader engine/UI/docs against canonical spec, plan next improvements (permissions UX, UI data sources, logging, research refresh).
