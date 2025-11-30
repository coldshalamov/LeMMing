# LeMMing: Lightweight Multi-Model Engine

LeMMing (Lightweight Multi-Model Engine) is a filesystem-first multi-agent orchestration framework. It simulates an organization of LLM workers that communicate solely via permissioned outboxes and run in discrete turns.

## Features
- Agents have persistent memory, logs, and resume-driven instructions.
- Org chart enforces who can read and write to each other.
- Credits and speed multipliers control execution cost and cadence.
- Uses the OpenAI API via model registry.
- CLI for bootstrapping and running the engine.

## Requirements
- Python >= 3.11
- An `OPENAI_API_KEY` environment variable with access to the configured OpenAI models.

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
│   ├── file_dispatcher.py # Filesystem helpers
│   └── config/            # Default configs
├── agents/                # Agent folders (resume, outbox, memory, logs)
├── ui/lemming_dashboard.html # Static dashboard placeholder
└── pyproject.toml
```

## Notes
- Agents only write to their own outboxes. Reading others' outboxes simulates inboxes according to the org chart.
- Credits are deducted per model call and persisted to `lemming/config/credits.json`.
- The Manager agent is the primary interface for human interaction and periodic summaries.
