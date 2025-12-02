# PROJECT_RULES

## Architectural Mandates ("New World Order")
1. **Resume-Driven:** Each agent must load configuration, permissions, schedule, and tools exclusively from `agents/<name>/resume.json`.
2. **Outbox-Only Messaging:** Agents never write into other agents' folders. An agent writes to its own `outbox/`, and peers read from that location if permitted.
3. **Tick-Based Scheduling:** Replace continuous loops with tick-based execution: `run_if: (tick % run_every_n) == phase_offset`.
4. **No Central Org Chart:** The organization graph is derived dynamically from agent resumes, not from any central configuration file.
5. **Generic Engine:** The engine remains role-agnostic; it orchestrates generic agents defined by JSON without hardcoded notions of roles.

## Safety & Constraints
- Enforce strict handling of LLM JSON outputs: never crash on malformed JSON; log issues and continue.
- Never delete user data in `agents/` without explicit confirmation.
- Avoid adding new dependencies without approval.
- Maintain scope focus on the refactor plan; do not add unrelated improvements.
