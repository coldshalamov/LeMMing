## Handoff prompt for next Codex CLI instance

Current state (2025-12-14 ~05:45 ET):
- Repo at `C:\Users\User\Documents\GitHub\Telomere\LeMMing`.
- Tests are green: `.venv\Scripts\python -m pytest` passes (37/37).
- Canonical spec: `LEMMING_SOURCE_OF_TRUTH.md` created/updated; whitepaper and docs already in `docs/`.
- Lab notebook: `dev_bus/lab_notebook.md` records bootstrap, baseline failures, and fixes.
- Code changes: `lemming/agents.py` now has sane defaults (AgentModel/Schedule/Permissions/Credits/FileAccess), credits defaulting, relaxed instructions requirement; this unblocked scheduler/permissions/CLI/API/credits tests.

Recommended next actions (pick the top priority first):
1) Engine audit vs spec: verify permission canonicalization, tool enforcement, logging (structured events), tick loop determinism; tighten anything missing from `LEMMING_SOURCE_OF_TRUTH.md`.
2) UI audit: ensure dashboard surfaces agents, ticks, outboxes, memory, tool calls, graphs; verify data sources align with engine outputs; add API endpoints if gaps exist.
3) Research refresh: gather human evidence on multi-agent orchestration/determinism/permissions and log takeaways in `dev_bus/RESEARCH_NOTES.md`.
4) Docs: update docs with new defaults (model/credits), how to add agents, run UI/tests; link to spec.
5) Integration polish: consider golden-run snapshot test, permission edge cases, tool path canonicalization tests.

Context reminders:
- Time-based rule: at 06:30 AM America/New_York, invoke Claude Code CLI as adversarial auditor; persist critiques.
- Stop condition: at 08:00 AM ET, produce final status report with resume commands.

Suggested first task now: Perform a focused engine/permissions audit (tools.py path allowlist, org credit flow, engine logging) and patch any spec gaps; then document in lab notebook and update spec if needed.
