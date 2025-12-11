# 🤖 LeMMing: Lightweight Multi-Model Engine

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

LeMMing is a **filesystem-first multi-agent orchestration framework** that simulates an organization of LLM workers communicating via permissioned outboxes in discrete ticks.

## ✨ Key Features

- 📄 **Resume as ABI** - Agent configuration via `resume.json` files
- 📬 **Outbox-Only Messaging** - Agents communicate through `OutboxEntry` messages in their outboxes
- ⏱️ **Tick-Based Scheduler** - Deterministic execution with configurable `run_every_n_ticks` and `phase_offset`
- 🌐 **Multi-Provider Support** - OpenAI, Anthropic Claude, and Ollama local models
- 💰 **Credit System** - Cost control with per-agent credit tracking
- 🧪 **Comprehensive Testing** - Test suite with high coverage
- 🐳 **Docker Ready** - Containerized deployment with docker-compose
- 🔄 **CI/CD** - GitHub Actions for automated testing and builds

## 📋 Requirements

- Python >= 3.11
- Optional: API keys for your chosen LLM providers
  - `OPENAI_API_KEY` for OpenAI models
  - `ANTHROPIC_API_KEY` for Claude models
  - Ollama installed for local models

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration
Default configuration lives under `lemming/config`. The `bootstrap` command will create any missing files and agent folders.

Set your OpenAI API key before running:
```bash
export OPENAI_API_KEY=your_api_key_here
```

## Usage

### Quickstart

```bash
cp -r agents/agent_template agents/my_agent
python -m lemming.cli bootstrap
python -m lemming.cli run
```

### Core Commands

Bootstrap the framework (idempotent):
```bash
python -m lemming.cli bootstrap
```

Run the engine continuously:
```bash
python -m lemming.cli run
```

Run a single tick (useful for testing):
```bash
python -m lemming.cli run-once
```

Validate configs and resumes before running:
```bash
python -m lemming.cli validate
```

### Monitoring Commands

View organization status:
```bash
python -m lemming.cli status
```

View agent logs:
```bash
python -m lemming.cli logs <agent_name>
python -m lemming.cli logs <agent_name> --lines 50
```

Inspect agent details:
```bash
python -m lemming.cli inspect <agent_name>
```

### API Server & Dashboard

Start the API server and live dashboard:
```bash
python -m lemming.cli serve
```

Access the dashboard at `http://localhost:8000/dashboard` and API docs at `http://localhost:8000/docs`.

Custom host/port:
```bash
python -m lemming.cli serve --host 127.0.0.1 --port 8080
```

The API provides endpoints for:
- `/api/agents` - List all agents
- `/api/agents/{name}` - Get agent details
- `/api/messages` - List messages
- `/api/credits` - Get credits information
- `/api/status` - System status
- `/ws` - WebSocket for real-time updates

### Resume Format (Agent Contract)

Resumes are the filesystem ABI between humans and agents. Each `agents/<name>/resume.json` defines the agent:

```json
{
  "name": "agent_name",
  "title": "Agent Title",
  "short_description": "Brief description of agent purpose",
  "workflow_description": "Detailed workflow and responsibilities",
  "instructions": "Specific instructions for the LLM",
  "model": "gpt-4.1-mini",
  "permissions": {
    "read_outboxes": ["other_agent"],
    "tools": ["tool1", "tool2"]
  },
  "schedule": {
    "run_every_n_ticks": 1,
    "phase_offset": 0
  }
}
```

See `agents/agent_template/` for a canonical example.

### Example Agents

- `spec_writer` – compiles a periodic snapshot of org decisions into its memory
- `log_summarizer` – turns engine logs and outbox highlights into digestible updates
- `ui_copy_editor` – suggests clearer phrasing for API or UI change notes

## Project Layout
```
LeMMing/
├── lemming/               # Python package
│   ├── cli.py             # CLI entry points
│   ├── engine.py          # Tick-based scheduler
│   ├── messages.py        # OutboxEntry message format
│   ├── agents.py          # Agent loading/parsing helpers
│   ├── models.py          # Model registry + provider wrappers
│   ├── org.py             # Org graph, config, credits
│   ├── memory.py          # Agent memory system
│   ├── api.py             # FastAPI backend server
│   └── config/            # Default configs
│       ├── credits.json   # Per-agent credit tracking
│       ├── models.json    # Model provider configurations
│       └── org_config.json # Global org settings
├── agents/                # Agent folders (resume, outbox, memory, logs)
│   └── agent_template/    # Canonical agent example
├── tests/                 # Comprehensive test suite
├── ui/                    # Dashboard UIs
├── Makefile               # Common development commands
└── pyproject.toml
```

## 🏗️ Architecture

### Core Principles

1. **Resume as ABI**: Every agent is defined by `agents/<name>/resume.json`. This file contains all configuration, permissions, scheduling, and instructions.

2. **Outbox-Only Messaging**: Agents never write to other agents' directories. Instead:
   - Each agent writes `OutboxEntry` messages to its own `agents/<name>/outbox/`
   - Other agents read permitted outboxes to build a virtual inbox
   - Message format is defined in `lemming.messages.OutboxEntry`

3. **Tick-Based Scheduling**: The engine runs in discrete ticks:
   - Global tick counter increments each cycle
   - Agent runs when: `(tick % run_every_n_ticks) == (phase_offset % run_every_n_ticks)`
   - Configured via `schedule` in resume.json

4. **No Central Org Chart**: The permission graph is derived dynamically from resume.json files. No `org_chart.json` exists as authoritative config.

5. **Filesystem Transparency**: Everything important is a file: resumes, outboxes, memory, configs, logs. Git-trackable and human-readable.

## 🚀 Creating Your First Agent

1. Copy the template:
```bash
cp -r agents/agent_template agents/my_agent
```

2. Edit `agents/my_agent/resume.json`:
   - Set `name` to "my_agent"
   - Customize `title`, `short_description`, `instructions`
   - Configure `permissions.read_outboxes` for which agents to read from
   - Set `schedule.run_every_n_ticks` for execution frequency

3. Update `lemming/config/credits.json`:
```json
{
  "my_agent": {
    "model": "gpt-4.1-mini",
    "cost_per_action": 0.01,
    "credits_left": 100.0
  }
}
```

4. Bootstrap and run:
```bash
python -m lemming.cli bootstrap
python -m lemming.cli run
```

## 🐳 Docker Deployment

Run LeMMing with Docker:

```bash
# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

The docker-compose setup runs both the API server (port 8000) and the engine.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- Run tests: `make test`
- Format code: `make format`
- Lint code: `make lint`
- All checks: `make check-all`

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Documentation

- [ROADMAP.md](ROADMAP.md) - Development roadmap and planned features
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [PROJECT_RULES.md](PROJECT_RULES.md) - Architectural mandates
- API Docs: Run `python -m lemming.cli serve` and visit `/docs`

## Notes

- Agents communicate solely via `OutboxEntry` messages in their outboxes
- Credits are deducted per model call and persisted to `lemming/config/credits.json`
- Tick-based execution ensures deterministic behavior and easy debugging
- The framework is role-agnostic - define your organization structure via resume.json files
