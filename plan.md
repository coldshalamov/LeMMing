# plan.md

## OVERVIEW
LeMMing is a filesystem-first multi-agent orchestration engine at v1.0.0. Each agent is defined by `agents/<name>/resume.json`, communicates via JSON `OutboxEntry` files in its own `outbox/`, and runs on a deterministic tick scheduler. The system is production-ready with comprehensive testing, multi-provider support, CLI tools, API/UI stack, and clean architecture aligned with PROJECT_RULES.md.

## CURRENT STATE (v1.0.0)
- **Core Architecture:** resume-as-ABI, outbox-only messaging, tick-based scheduling, permission-derived graph
- **Code Quality:** 32+ tests passing, lint clean (ruff), type clean (mypy), CI configured
- **Providers:** OpenAI, Anthropic Claude, Ollama with retry/circuit breaker patterns
- **CLI:** 15+ commands including bootstrap, run, validate, status, inspect, logs, send, inbox, chat, serve
- **API:** FastAPI backend with WebSocket support for real-time updates
- **UI:** Next.js dashboard for agent monitoring and message visualization
- **Memory:** Per-agent memory system with CRUD operations, archiving, compaction
- **Tools:** Extensible tool framework with permission enforcement (file ops, shell, memory, agent creation)
- **Credits:** Per-agent credit tracking with cost deduction and soft caps
- **Documentation:** README, PROJECT_RULES, ROADMAP, CONTRIBUTING, docs/

## COMPLETED WORK
### Phase 1: Core Hardening ✅
- Resume.json enforced as canonical (resume.txt deprecated with warning)
- Test failures fixed (logging improvements)
- Lint and type errors resolved
- send_outboxes made optional (removed from defaults)
- All architecture invariants enforced

### Earlier Phases (Already Complete)
- Testing infrastructure with pytest, fixtures, mocking
- Code quality tools: ruff, black, mypy, coverage
- Human-in-the-loop CLI (send, inbox, chat commands)
- Memory system with persistent storage
- Multi-provider abstraction (OpenAI, Anthropic, Ollama)
- Tool framework with permissions
- FastAPI backend with WebSocket
- Dashboard UI (Next.js)
- Docker and docker-compose support
- Structured logging (JSON lines)
- Configuration validation
- CI/CD pipeline

## REMAINING ENHANCEMENTS (Post-v1.0)
Optional improvements for future versions:
- Vector database integration for memory search (chromadb)
- Enhanced dashboard visualizations (org graph, message flow animation)
- Message threading and reply-to support
- Additional tools (web search, code sandbox)
- Multi-organization support
- Agent marketplace/templates
- Advanced monitoring/metrics (Prometheus)

## NON-GOALS
- Centralized databases replacing filesystem (filesystem-first is core principle)
- Push-style messaging or direct agent-to-agent writes (violates outbox architecture)
- Hardcoded role hierarchies (permission-derived only)
- Backwards compatibility for deprecated features (resume.txt, org_chart.json)

## ARCHITECTURE NOTES
### Scheduling
`should_run(agent, tick)` returns true when: `(tick + (offset % N)) % N == 0` where N is `run_every_n_ticks`
Fire point calculation ensures deterministic ordering: `fire_point = ((-offset) % N) / N`

### Outbox Format
```json
{
  "id": "uuid",
  "tick": 123,
  "agent": "sender_name",
  "kind": "message|report|request|response|status",
  "payload": {"text": "...", ...},
  "tags": ["optional"],
  "recipients": ["target1", "target2"] | null,
  "created_at": "ISO8601",
  "meta": {...}
}
```

### Engine Contract
LLM must respond with:
```json
{
  "outbox_entries": [...],
  "tool_calls": [...],
  "memory_updates": [...],
  "notes": "..."
}
```
All fields optional; engine is tolerant and logs violations.

## RISKS & MITIGATIONS
- **Path traversal:** Tool framework canonicalizes paths and enforces allow lists
- **Credit races:** File-based locking could be added if concurrent engines needed
- **LLM output drift:** Strict logging and contract violation detection in place
- **Dashboard/API divergence:** WebSocket schema is stable and tested

## SUCCESS CRITERIA
All met for v1.0.0:
✅ All tests pass (32/32)
✅ Lint and type checks clean
✅ Documentation matches implementation
✅ CLI commands work as documented
✅ API endpoints functional
✅ Multi-provider support works
✅ Example agents demonstrate patterns
✅ CI/CD pipeline runs on PRs
