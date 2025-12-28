# LeMMing Development Plan

## Current Position
**Phase 1 in progress** - Core engine & messaging hardening

Based on existing `workflow_state.md` and `plan.md`, the project is mid-Phase 1 with:
- ✅ Resume ABI locked to JSON-only
- ✅ Permissions simplified to `read_outboxes` + `tools`
- ✅ File tools sandboxed to workspace/shared
- ❌ Remaining doc cleanup needed
- ❌ Scheduler/messaging docs need hardening
- ❌ Additional validation/tests needed

## Phased Roadmap

### Phase 1: Core Engine & Messaging Hardening (CURRENT - MUST-have)
- [x] Lock resume ABI to JSON only (drop resume.txt)
- [x] Simplify permissions to `read_outboxes` and `tools`
- [x] Sandbox file tools to workspace/shared
- [ ] Sweep remaining docs for legacy `file_access` mentions
- [ ] Harden scheduler/messaging docs for tick-based invariants
- [ ] Expand validation/tests for new resume schema

### Phase 2: Tests, Config Validation, Logging (MUST-have)
- [ ] Expand pytest coverage for new invariants
- [ ] Add schema/validation helpers for resumes and configs
- [ ] Harden logging with structured context
- [ ] Error resilience in LLM output parsing

### Phase 3: Human-in-the-Loop CLI (MUST-have)
- [ ] `lemming send <agent> <message>` command
- [ ] `lemming chat` interactive REPL
- [ ] Human agent template with inbox view
- [ ] Message history filters

### Phase 4: Real-time Dashboard & API (MUST-have)
- [ ] Wire dashboard to REST API instead of static data
- [ ] WebSocket for live updates
- [ ] Interactive org chart visualization
- [ ] API tests for new endpoints

### Phase 5: Production Polish (NICE-to-have)
- [ ] Additional LLM providers (Azure, Gemini)
- [ ] Advanced tool capabilities
- [ ] Production deployment manifests
- [ ] Comprehensive documentation

## Immediate Next Actions
See `.agent/brain/NEXT.md` for the next concrete chunk of work.

## Non-Goals
- Introducing centralized databases (filesystem-first principle)
- Restoring deprecated push-style outbox layouts
- Hardcoded role hierarchies
- Supporting legacy resume.txt
