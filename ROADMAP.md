# LeMMing Development Roadmap

**Version:** 1.0.0
**Status:** Near v1.0 - Production-Ready Multi-Agent Orchestration Engine
**Last Updated:** December 2024

---

## Current State (v1.0.0)

✅ **Core Infrastructure**
- Core multi-agent orchestration engine
- Filesystem-based messaging via outboxes
- Tick-based scheduler with deterministic ordering
- Resume.json as canonical agent ABI
- Credit/cost management system
- Per-agent memory system with CRUD operations
- Tool framework with permission enforcement

✅ **Testing & Quality**
- Comprehensive test suite (32+ tests)
- High test coverage for core modules
- Linting with ruff
- Type checking with mypy
- CI/CD with GitHub Actions

✅ **CLI Features**
- Agent management (bootstrap, list, show, inspect)
- Execution control (run, run-once, status)
- Human interaction (send, inbox, chat)
- Monitoring (logs, status, derive-graph)
- Validation (validate configs and resumes)

✅ **API & Dashboard**
- FastAPI backend with REST endpoints
- WebSocket support for live updates
- Dashboard UI (Next.js based)
- Agent status and message monitoring

✅ **Multi-Provider Support**
- OpenAI (GPT-4, GPT-3.5, etc.)
- Anthropic Claude (claude-3-5-sonnet, etc.)
- Ollama (local models)
- Extensible provider system with retry/circuit breaker

✅ **Production Features**
- Docker & docker-compose support
- Structured logging (JSON lines)
- Error handling and resilience
- Configuration validation
- Migration tools

---

## What's Next (Post-v1.0)

### Near-term Enhancements
- Vector database integration for agent memory (chromadb)
- Advanced tool capabilities (web search, code execution)
- Dynamic agent creation from HR agent
- Message threading and reply-to support
- Enhanced dashboard visualizations

### Long-term Vision
- Agent marketplace (share/import agents)
- Multi-modal agents (image/audio processing)
- Integration with external services (Slack, Discord, GitHub)
- Agent learning from feedback
- Cost optimization recommendations

---

## Architecture Highlights

### Resume as ABI
Every agent is defined by `agents/<name>/resume.json` containing:
- Agent metadata (name, title, description)
- Model configuration (key, temperature, max_tokens)
- Permissions (read_outboxes, tools, optional send_outboxes, file_access)
- Scheduling (run_every_n_ticks, phase_offset)
- Credits (max_credits, soft_cap)
- Instructions for the LLM

### Outbox-Only Messaging
- Agents write JSON `OutboxEntry` messages to their own `outbox/`
- Other agents read permitted outboxes to build virtual inbox
- No direct agent-to-agent file writes
- Messages include: id, tick, agent, kind, payload, tags, recipients, created_at

### Tick-Based Scheduler
- Global tick counter increments each cycle
- Agent runs when: `(tick % run_every_n_ticks) == (phase_offset % run_every_n_ticks)`
- Deterministic execution order via fire_point calculation
- Configurable tick duration via org_config.json

### Tool Framework
- Agents request tools via permissions.tools in resume
- Tools validate permissions before execution
- Built-in tools: file_read, file_write, file_list, shell, memory_read, memory_write, create_agent, list_agents
- File access controls prevent directory escapes

---

## Migration Guide (v0.x → v1.0)

### Resume Format
- **Old:** `resume.txt` with `[INSTRUCTIONS]` and `[CONFIG]` sections
- **New:** `resume.json` with full JSON structure
- Migration tool: `python -m lemming.cli migrate-resumes`
- Loader still supports .txt (with deprecation warning) for backward compatibility

### API Changes
- `send_outboxes` is now optional (defaults to None = unrestricted)
- `file_access` permissions are now structured with allow_read/allow_write lists
- Agent discovery ignores `agent_template` directory

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

### Development Workflow
```bash
# Install dev dependencies
pip install -e ".[dev,api,llm]"

# Run tests
make test

# Run all checks (lint, typecheck, test)
make check-all

# Format code
make format
```

### Adding a New Provider
1. Inherit from `lemming.providers.LLMProvider`
2. Implement `call(model_name, messages, temperature, **kwargs)` method
3. Register provider: `register_provider("provider_name", YourProvider)`
4. Update `lemming/config/models.json` with provider mappings

### Creating a New Tool
1. Inherit from `lemming.tools.Tool`
2. Set `name` and `description` class attributes
3. Implement `execute(agent_name, base_path, **kwargs)` method
4. Register tool: `ToolRegistry.register(YourTool())`
5. Add tool name to agent's `permissions.tools` in resume.json

---

## License

MIT License - see [LICENSE](LICENSE) file for details.
