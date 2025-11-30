# LeMMing Development Roadmap

**Version:** 1.0
**Status:** v0.1.0 → v1.0.0
**Timeline:** 5 Phases

---

## Current State (v0.1.0)

✅ Core multi-agent orchestration engine
✅ Filesystem-based messaging via outboxes
✅ Org chart permission system
✅ Credit/cost management
✅ Resume-based agent configuration
✅ Turn-based execution loop
✅ Basic CLI (bootstrap, run, run-once)
✅ 5 default agents (manager, planner, hr, coder_01, janitor)

❌ No tests
❌ No human interaction
❌ Static dashboard only
❌ Single provider (OpenAI only)
❌ Limited observability
❌ No error recovery

---

## Phase 1: Foundation & Testing Infrastructure

**Goal:** Establish code quality foundation and developer tooling
**Version:** v0.2.0

### 1.1 Testing Infrastructure
- [ ] Add pytest as dev dependency
- [ ] Create `tests/` directory structure
- [ ] Add `conftest.py` with fixtures (mock agents, temp directories)
- [ ] Mock OpenAI client for testing
- [ ] Unit tests for `messaging.py` (100% coverage)
- [ ] Unit tests for `org.py` (100% coverage)
- [ ] Unit tests for `agents.py` (100% coverage)
- [ ] Unit tests for `models.py` (100% coverage)
- [ ] Integration tests for `engine.py`
- [ ] Test utilities and helpers

### 1.2 Code Quality Tools
- [ ] Add `ruff` for linting
- [ ] Add `black` for formatting
- [ ] Add `mypy` for type checking
- [ ] Add `pytest-cov` for coverage reporting
- [ ] Create `pyproject.toml` dev dependencies section
- [ ] Add `Makefile` with common commands (test, lint, format)
- [ ] Pre-commit hooks configuration

### 1.3 Configuration Validation
- [ ] JSON schema files for all config files
- [ ] Validation on bootstrap
- [ ] Validation on config load
- [ ] Better error messages for invalid configs
- [ ] Config migration system

### 1.4 Better Logging
- [ ] Structured logging with context (agent name, turn number)
- [ ] Log levels per module
- [ ] JSON log output option
- [ ] Separate log files per agent
- [ ] Log rotation

**Deliverables:** Test suite, linting setup, validated configs, better logs

---

## Phase 2: Human Interaction & Core Features

**Goal:** Make LeMMing interactive and usable for real tasks
**Version:** v0.3.0

### 2.1 Human-in-the-Loop CLI
- [ ] `lemming send <agent> <message>` command
- [ ] `lemming chat` interactive REPL mode
- [ ] `lemming inbox` view messages for user
- [ ] Create virtual "human" agent in org chart
- [ ] Human agent directory structure
- [ ] Manager can send to human
- [ ] Rich CLI formatting (colors, tables)
- [ ] Message history view

### 2.2 Enhanced CLI Commands
- [ ] `lemming status` - show org health, credits, active agents
- [ ] `lemming logs <agent>` - tail agent logs
- [ ] `lemming inspect <agent>` - show agent details
- [ ] `lemming reset` - reset org state
- [ ] `lemming top-up <agent> <credits>` - add credits
- [ ] `lemming pause` / `lemming resume` - control execution
- [ ] Turn-by-turn stepping mode

### 2.3 Message Enhancements
- [ ] Message priorities (urgent, normal, low)
- [ ] Message threading/reply-to
- [ ] Message reactions/acknowledgments
- [ ] Broadcast messages
- [ ] Message search functionality
- [ ] Archive instead of delete

### 2.4 Agent Memory System
- [ ] Persistent memory directory per agent
- [ ] Memory read/write in agent instructions
- [ ] Memory summary on agent init
- [ ] Vector DB integration (optional, using chromadb)
- [ ] Memory search capabilities

**Deliverables:** Interactive CLI, human agent, message improvements, memory system

---

## Phase 3: Dashboard & API Backend

**Goal:** Real-time visualization and monitoring
**Version:** v0.4.0

### 3.1 REST API Backend
- [ ] FastAPI application structure
- [ ] `/api/agents` - list all agents
- [ ] `/api/agents/{name}` - agent details
- [ ] `/api/messages` - message history
- [ ] `/api/messages?agent={name}` - agent-specific messages
- [ ] `/api/credits` - credits status
- [ ] `/api/org-chart` - org structure
- [ ] `/api/status` - system health
- [ ] CORS configuration
- [ ] API authentication (API key)

### 3.2 WebSocket Support
- [ ] WebSocket endpoint for live updates
- [ ] Broadcast turn completions
- [ ] Broadcast new messages
- [ ] Agent status changes
- [ ] Real-time log streaming

### 3.3 Enhanced Dashboard UI
- [ ] Connect to REST API instead of static data
- [ ] Real-time updates via WebSocket
- [ ] Interactive org chart visualization (D3.js/mermaid)
- [ ] Message flow animation
- [ ] Agent activity timeline
- [ ] Credit usage graphs (Chart.js)
- [ ] Message browser with search
- [ ] Agent configuration editor
- [ ] Dark mode toggle

### 3.4 Monitoring & Metrics
- [ ] Prometheus metrics export
- [ ] Turn duration tracking
- [ ] Message count metrics
- [ ] Credit usage metrics
- [ ] API call success/failure rates
- [ ] Agent activity heatmap

**Deliverables:** FastAPI backend, WebSocket support, interactive dashboard, metrics

---

## Phase 4: Multi-Provider & Advanced Agent Capabilities

**Goal:** Provider flexibility and agent superpowers
**Version:** v0.5.0

### 4.1 Abstract LLM Interface
- [ ] Provider abstraction layer
- [ ] Provider registry system
- [ ] Provider-specific configuration
- [ ] Fallback provider mechanism
- [ ] Cost tracking per provider

### 4.2 Additional LLM Providers
- [ ] Anthropic Claude support (claude-3-5-sonnet, etc.)
- [ ] Azure OpenAI support
- [ ] Local model support (Ollama)
- [ ] Google Gemini support
- [ ] Custom provider plugin system
- [ ] Provider health checks

### 4.3 Agent Tool Calling
- [ ] Tool/function calling framework
- [ ] Filesystem tools (read, write, list, search)
- [ ] Shell command execution tools
- [ ] Python code execution (sandbox)
- [ ] Web search tool
- [ ] Calculator tool
- [ ] Custom tool registration
- [ ] Tool permission system

### 4.4 Advanced Agent Features
- [ ] Dynamic agent creation (HR can spawn agents)
- [ ] Agent templates library
- [ ] Agent inheritance/composition
- [ ] Specialized agent types (Tester, Reviewer, QA)
- [ ] Agent collaboration patterns
- [ ] Parallel agent execution
- [ ] Agent state checkpointing

### 4.5 Smart Message Routing
- [ ] Priority queues per agent
- [ ] Message routing rules
- [ ] Auto-escalation
- [ ] Message aggregation
- [ ] Intelligent message batching

**Deliverables:** Multi-provider support, tool calling, advanced agents, smart routing

---

## Phase 5: Production Features & Polish

**Goal:** Production-ready, scalable, maintainable
**Version:** v1.0.0

### 5.1 Database Backend (Optional)
- [ ] SQLite integration for message history
- [ ] State persistence to DB
- [ ] Migration from filesystem
- [ ] Hybrid mode (filesystem + DB)
- [ ] Query optimization
- [ ] Full-text search

### 5.2 Error Handling & Resilience
- [ ] Retry logic with exponential backoff
- [ ] Circuit breakers for API calls
- [ ] Graceful degradation
- [ ] Error recovery mechanisms
- [ ] Dead letter queue for failed messages
- [ ] Automatic credit top-up warnings

### 5.3 Security & Safety
- [ ] API key rotation
- [ ] Secret management (environment vars, vault)
- [ ] Rate limiting per agent
- [ ] Input sanitization
- [ ] Audit logging
- [ ] Agent sandbox isolation
- [ ] Permission scoping

### 5.4 Deployment & Operations
- [ ] Dockerfile for containerization
- [ ] Docker Compose for full stack
- [ ] Kubernetes manifests
- [ ] Health check endpoints
- [ ] Graceful shutdown handling
- [ ] Environment-based configuration
- [ ] Production vs development modes
- [ ] Systemd service file

### 5.5 Documentation
- [ ] Architecture documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Agent development guide
- [ ] Tutorial: Creating custom agents
- [ ] Tutorial: Adding new tools
- [ ] Troubleshooting guide
- [ ] Example use cases
- [ ] Video walkthrough

### 5.6 Advanced Features
- [ ] Multi-organization support
- [ ] Organization templates
- [ ] Simulation mode (dry-run)
- [ ] A/B testing framework
- [ ] Agent performance analytics
- [ ] Export/import org state
- [ ] Backup and restore

### 5.7 CI/CD Pipeline
- [ ] GitHub Actions workflow
- [ ] Automated testing on PR
- [ ] Linting and type checking
- [ ] Coverage reporting
- [ ] Automated releases
- [ ] Changelog generation
- [ ] Docker image publishing

**Deliverables:** Production-ready system, deployment configs, comprehensive docs, CI/CD

---

## Success Metrics

### v0.2.0 (Phase 1)
- ✓ 90%+ test coverage
- ✓ All code passes linting and type checking
- ✓ Zero config validation errors

### v0.3.0 (Phase 2)
- ✓ Can send messages to agents via CLI
- ✓ Interactive chat mode works
- ✓ Agents can message human back
- ✓ Memory system stores context

### v0.4.0 (Phase 3)
- ✓ Dashboard shows real-time data
- ✓ Can monitor agent activity live
- ✓ Message flow visualization works
- ✓ API documented and tested

### v0.5.0 (Phase 4)
- ✓ Can switch between OpenAI and Claude
- ✓ Agents can execute tools
- ✓ Can dynamically create new agents
- ✓ Parallel execution reduces latency

### v1.0.0 (Phase 5)
- ✓ Runs in production with uptime
- ✓ Comprehensive documentation
- ✓ CI/CD pipeline operational
- ✓ Community-ready for contributions

---

## Implementation Order

Each phase builds on the previous:

1. **Phase 1** - Foundation first (can't build on shaky ground)
2. **Phase 2** - Make it usable (human interaction is critical)
3. **Phase 3** - Make it visible (observability matters)
4. **Phase 4** - Make it powerful (advanced capabilities)
5. **Phase 5** - Make it production-ready (polish and scale)

**Estimated Total Time:** 20-30 hours of focused development

---

## Post-1.0 Ideas

- Agent marketplace (share/import agents)
- Agent emotions/morale simulation
- Self-improving agents
- Multi-modal agents (image/audio processing)
- Integration with external services (Slack, Discord, GitHub)
- Agent learning from feedback
- Automated agent optimization
- Cost optimization recommendations

---

## Questions to Decide

1. **Database:** Should we add SQLite or stay filesystem-only?
2. **Providers:** Which LLM providers are priority? (Claude, Ollama, Azure?)
3. **Tools:** Which tools should agents have access to?
4. **Security:** How strict should agent sandboxing be?
5. **Deployment:** Target deployment environment? (local, cloud, both?)

---

**Ready to build? Let's start with Phase 1!**
