# Workflow State

## Current Task
✅ **COMPLETE:** LeMMing v1.0 audit and hardening finished.

The repository is now in a clean, production-ready state with:
- All tests passing (32/32)
- Lint and type checks clean
- Resume.json as canonical ABI
- Comprehensive documentation
- Multi-provider support (OpenAI, Anthropic, Ollama)
- Full CLI and API capabilities

## Architecture Status

### ✅ Core Invariants Enforced
- **Resume as ABI**: `resume.json` is canonical, `.txt` deprecated with warning
- **Outbox-only messaging**: Agents write to own outbox, others read via permissions
- **Tick-based scheduling**: Deterministic execution with fire_point ordering
- **Filesystem transparency**: All state in files (resumes, outboxes, memory, configs, logs)
- **Permission-derived graph**: No central org chart, derived from resumes

### ✅ Implementation Quality
- Engine contract normalization: robust JSON parsing with logging
- Credit system: per-agent tracking with deduction
- Memory system: CRUD operations with archiving and compaction
- Tool framework: permission-based access with file safety
- Provider abstraction: OpenAI, Anthropic, Ollama with retry/circuit breaker

### ✅ Testing & CI
- Comprehensive test suite covering:
  - Agent loading and validation
  - Engine contract parsing
  - Scheduler fire_point calculation
  - Message I/O and permissions
  - Tool permissions
  - API endpoints
  - CLI commands
- All checks pass: pytest, ruff, mypy
- GitHub Actions CI configured

## Repository Summary
A filesystem-first multi-agent framework with:
- **Core:** Engine, scheduler, messaging, memory, tools, providers
- **Config:** models.json, credits.json, org_config.json in lemming/config/
- **Agents:** agent_template + example agents (human, spec_writer, log_summarizer, ui_copy_editor)
- **CLI:** 15+ commands for management, execution, and monitoring
- **API:** FastAPI backend with WebSocket support
- **UI:** Next.js dashboard under ui/
- **Tests:** Full coverage in tests/
- **Docs:** README, PROJECT_RULES, ROADMAP, CONTRIBUTING, docs/

## No Open Questions
System is stable and ready for use.
