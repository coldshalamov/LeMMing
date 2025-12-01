# 🤖 LeMMing: Lightweight Multi-Model Engine

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

LeMMing is a **filesystem-first multi-agent orchestration framework** that simulates an organization of LLM workers communicating via permissioned outboxes in discrete turns.

## ✨ Key Features

- 🏢 **Org Chart Permissions** - Hierarchical communication via send_to/read_from permissions
- 💬 **Human-in-the-Loop** - Interactive CLI for chatting with agents and viewing messages
- 🌐 **Multi-Provider Support** - OpenAI, Anthropic Claude, and Ollama local models
- 📊 **Live Dashboard** - Real-time web UI with FastAPI and WebSocket updates
- 💾 **Persistent Memory** - Agent memory system for context retention
- 💰 **Credit System** - Cost control with per-agent credit tracking
- ⚡ **Speed Multipliers** - Control agent execution frequency
- 🧪 **Comprehensive Testing** - 72 tests with high coverage
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

### Core Commands

Bootstrap the org and agents (idempotent):
```bash
python -m lemming.cli bootstrap
```

Run the engine continuously:
```bash
python -m lemming.cli run
```

Run a single turn (useful for testing):
```bash
python -m lemming.cli run-once
```

Validate configs and resumes before running (great for CI or new orgs):
```bash
python -m lemming.cli validate
```

### Human Interaction Commands

Send a message to an agent:
```bash
python -m lemming.cli send manager "Hello, what's the status?"
python -m lemming.cli send manager "Urgent task" --importance high
```

View your inbox:
```bash
python -m lemming.cli inbox
```

Interactive chat with an agent:
```bash
python -m lemming.cli chat
python -m lemming.cli chat --agent planner
```

### Monitoring Commands

View organization status:
```bash
python -m lemming.cli status
```

View agent logs:
```bash
python -m lemming.cli logs manager
python -m lemming.cli logs coder_01 --lines 50
```

Inspect agent details:
```bash
python -m lemming.cli inspect manager
```

Add credits to an agent:
```bash
python -m lemming.cli top-up manager 100.0
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
- `/api/org-chart` - Get organization chart
- `/api/credits` - Get credits information
- `/api/status` - System status
- `/ws` - WebSocket for real-time updates

### Resume Format (Agent Contract)

Resumes are the filesystem ABI between humans and agents. Each `resume.txt` must include:

```
Name: <AGENT_NAME>
Role: <short role>
Description: <1–2 line summary>

[INSTRUCTIONS]
<guidance for the model>

[CONFIG]
{
  "model": "gpt-4.1-mini",
  "org_speed_multiplier": 1,
  "send_to": ["manager"],
  "read_from": ["manager"],
  "max_credits": 100.0
}
```

The `[CONFIG]` block is validated for required fields and types when the engine loads or when you run `lemming.cli validate`.

## Project Layout
```
LeMMing/
├── lemming/               # Python package
│   ├── cli.py             # CLI entry points
│   ├── engine.py          # Turn loop
│   ├── messaging.py       # Outbox-only messaging
│   ├── agents.py          # Agent loading/parsing helpers
│   ├── models.py          # Model registry + OpenAI wrapper
│   ├── org.py             # Org chart, config, credits
│   ├── memory.py          # Agent memory system
│   ├── api.py             # FastAPI backend server
│   ├── file_dispatcher.py # Filesystem helpers
│   └── config/            # Default configs
├── agents/                # Agent folders (resume, outbox, memory, logs)
│   └── human/             # Special human agent for user interaction
├── tests/                 # Comprehensive test suite
├── ui/                    # Dashboard UIs
│   ├── lemming_dashboard.html       # Static dashboard
│   └── lemming_dashboard_live.html  # Live dashboard with API
├── Makefile               # Common development commands
└── pyproject.toml
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
- API Docs: Run `python -m lemming.cli serve` and visit `/docs`

## Notes

- Agents communicate solely via outboxes - reading others' outboxes simulates inboxes
- Credits are deducted per model call and persisted to `lemming/config/credits.json`
- The Manager agent is the primary interface for human interaction
- Turn-based execution ensures deterministic behavior and easy debugging
