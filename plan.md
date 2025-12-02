# Migration Roadmap

1. **Analysis**: Scan existing `lemming/` modules to map current logic.
2. **Agent Loader**: Implement `Agent` class that loads strictly from `agents/<name>/resume.json`.
3. **Refactor Messaging**: Switch from `outbox/receiver/` (push) to pure `outbox/` (pull).
4. **Deprecate Org Chart**: Remove `org_chart.json` dependency; derive permissions from resumes.
5. **Implement Scheduler**: Replace speed multipliers with `run_every_n_ticks` and `phase_offset`.
6. **Schema Enforcement**: Enforce strict JSON output from LLMs (Outbox, Tool Calls, Memory).
7. **Tool & Memory Alignment**: Wire tools to permissions defined in `resume.json`.
8. **Generalize Agents**: Convert existing example agents to generic `resume.json` format.
9. **Update Interfaces**: Update CLI, API, and UI to reflect the new generic architecture.
10. **Test Coverage**: Update tests for the new scheduler and messaging model.
