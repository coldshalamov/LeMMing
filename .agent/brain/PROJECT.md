# LeMMing Project Summary

## What Is LeMMing?
**LeMMing** (Lightweight Multi-Model Engine) is a **filesystem-first multi-agent orchestration framework** that simulates an organization of LLM workers communicating via permissioned outboxes in discrete ticks.

### Core Philosophy
- **Resume as ABI**: Every agent is defined solely by `agents/<name>/resume.json`
- **Outbox-Only Messaging**: Agents write `OutboxEntry` messages to their own outbox; others read if permitted
- **Tick-Based Scheduler**: Deterministic execution with `run_every_n_ticks` and `phase_offset`
- **Filesystem Transparency**: All state (resumes, outboxes, memory, configs, logs) are human-readable files
- **No Central Org Chart**: Permission graph is derived dynamically from resume.json files

## Current State (v0.3-ish)
✅ **Implemented:**
- Core multi-agent orchestration engine with tick loop
- Filesystem-based messaging via outboxes
- Resume-based agent configuration (JSON format)
- Multi-provider support (OpenAI, Anthropic, Ollama)
- Credit/cost management per agent
- FastAPI backend + static dashboard
- Comprehensive test suite (17 test files)
- CLI: bootstrap, run, run-once, status, logs, inspect, top-up, validate, serve
- Docker support

❌ **Not Yet Complete:**
- Human-in-the-loop CLI (send/chat commands)
- Real-time dashboard (currently static)
- Full doc cleanup (legacy `file_access` references remain)
- Additional provider integrations
- Production hardening (circuit breakers, retry logic)

## Project Structure
```
LeMMing/
├── lemming/         # Core Python package (engine, CLI, API, tools, memory)
├── agents/          # Agent folders (resume.json, outbox/, memory/, logs/)
├── tests/           # Pytest suite (17 test files)
├── ui/              # Dashboard UI
├── docs/            # Documentation (11 files)
├── .agent/          # Agent workflow brain
└── pyproject.toml   # Project config
```

## Key Files
- `lemming/engine.py` - Tick-based scheduler and agent execution
- `lemming/agents.py` - Agent loading/parsing from resume.json
- `lemming/messages.py` - OutboxEntry message format
- `lemming/tools.py` - Sandboxed file/shell tools
- `lemming/api.py` - FastAPI backend + WebSocket
- `lemming/cli.py` - CLI entry points

## Tech Stack
- Python 3.11+
- FastAPI for API server
- Pytest for testing
- Docker/docker-compose for deployment
- LLM Providers: OpenAI, Anthropic, Ollama
