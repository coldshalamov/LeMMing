from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .engine import run_forever, run_once
from .org import reset_caches

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_RESUME_TEMPLATE = """Name: {name}
Role: {role}
Description: {description}

[INSTRUCTIONS]
{instructions}

[CONFIG]
{config}
"""


def write_resume(path: Path, name: str, role: str, description: str, instructions: str, config: dict) -> None:
    text = BASE_RESUME_TEMPLATE.format(
        name=name,
        role=role,
        description=description,
        instructions=instructions.strip(),
        config=json.dumps(config, indent=2),
    )
    path.write_text(text, encoding="utf-8")


def ensure_agent_dirs(agent_path: Path) -> None:
    for sub in ["outbox", "memory", "logs", "config"]:
        (agent_path / sub).mkdir(parents=True, exist_ok=True)


def bootstrap(base_path: Path) -> None:
    config_dir = base_path / "lemming" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    defaults = {
        "org_chart.json": {
            "manager": {
                "send_to": ["planner", "hr", "coder_01", "janitor"],
                "read_from": ["planner", "hr", "coder_01", "janitor"],
            },
            "planner": {"send_to": ["coder_01", "manager"], "read_from": ["manager", "coder_01"]},
            "hr": {"send_to": ["manager"], "read_from": ["manager"]},
            "coder_01": {"send_to": ["planner", "manager"], "read_from": ["planner"]},
            "janitor": {"send_to": ["manager"], "read_from": ["manager", "planner", "coder_01", "hr"]},
        },
        "credits.json": {
            "manager": {"model": "gpt-4.1-mini", "cost_per_action": 0.01, "credits_left": 100.0},
            "planner": {"model": "gpt-4.1-mini", "cost_per_action": 0.01, "credits_left": 100.0},
            "hr": {"model": "gpt-4.1-mini", "cost_per_action": 0.01, "credits_left": 100.0},
            "coder_01": {"model": "gpt-4.1", "cost_per_action": 0.03, "credits_left": 200.0},
            "janitor": {"model": "gpt-4.1-mini", "cost_per_action": 0.005, "credits_left": 50.0},
        },
        "org_config.json": {"base_turn_seconds": 10, "summary_every_n_turns": 12, "max_turns": None},
        "models.json": {
            "gpt-4.1": {"provider": "openai", "model_name": "gpt-4.1"},
            "gpt-4.1-mini": {"provider": "openai", "model_name": "gpt-4.1-mini"},
        },
    }

    for filename, content in defaults.items():
        path = config_dir / filename
        if not path.exists():
            path.write_text(json.dumps(content, indent=2), encoding="utf-8")
            logger.info("Created default config %s", path)

    # Agent template
    template_dir = base_path / "agents" / "agent_template"
    ensure_agent_dirs(template_dir)
    if not (template_dir / "resume.txt").exists():
        template_resume = """Name: TEMPLATE_AGENT
Role: Generic worker agent
Description: A generic LeMMing agent created from the template. Customize this resume for specific roles.

[INSTRUCTIONS]
You are a LeMMing agent. Follow your role description and respond with clear, structured outputs.
You receive messages from other agents and produce replies or actions.
Always respond in JSON following the protocol described in your CONFIG.

[CONFIG]
{
  "model": "gpt-4.1-mini",
  "org_speed_multiplier": 1,
  "send_to": [],
  "read_from": [],
  "max_credits": 50.0,
  "priority": "normal"
}
"""
        (template_dir / "resume.txt").write_text(template_resume, encoding="utf-8")
        logger.info("Created agent template resume")

    # Concrete agents
    agent_defs = {
        "manager": {
            "role": "Organization manager and user interface",
            "description": "Top-level agent that communicates with the human user and coordinates all other agents.",
            "instructions": """You are the Manager agent in the LeMMing organization.
You do NOT write code or perform low-level tasks directly.
Your jobs are:
- Interpret high-level user goals (from logs or future stdin integration).
- Communicate with Planner, HR, and other agents only through messages.
- Periodically summarize org status in a concise, human-readable way.
- When you respond, always output JSON:

{
  \"messages\": [
    {
      \"to\": \"<agent_name>\",
      \"content\": \"<text>\",
      \"importance\": \"normal\",
      \"ttl_turns\": 12
    }
  ],
  \"notes\": \"<free-form summary for logs>\"
}
""",
            "config": {
                "model": "gpt-4.1-mini",
                "org_speed_multiplier": 1,
                "send_to": ["planner", "hr", "coder_01", "janitor"],
                "read_from": ["planner", "hr", "coder_01", "janitor"],
                "max_credits": 100.0,
                "priority": "high",
            },
        },
        "planner": {
            "role": "Breaks goals into tasks and coordinates execution",
            "description": "Planner decomposes objectives, assigns work to coder_01, and reports progress to manager.",
            "instructions": """You are the Planner agent.
Analyze objectives from the Manager, break them into actionable tasks, and delegate to coder_01.
Report progress and blockers back to the Manager. Keep messages concise and actionable.
Always respond with JSON payloads containing messages and notes.
""",
            "config": {
                "model": "gpt-4.1-mini",
                "org_speed_multiplier": 1,
                "send_to": ["coder_01", "manager"],
                "read_from": ["manager", "coder_01"],
                "max_credits": 100.0,
                "priority": "high",
            },
        },
        "hr": {
            "role": "HR and org growth advisor",
            "description": "HR proposes new agents and monitors morale and capacity.",
            "instructions": """You are the HR agent.
Monitor the organization for staffing gaps and suggest new agents using the template.
You do not create agents directly but propose configurations to the Manager.
Always respond with JSON containing messages and notes.
""",
            "config": {
                "model": "gpt-4.1-mini",
                "org_speed_multiplier": 2,
                "send_to": ["manager"],
                "read_from": ["manager"],
                "max_credits": 100.0,
                "priority": "normal",
            },
        },
        "coder_01": {
            "role": "Primary coding agent",
            "description": "Implements tasks defined by Planner and reports technical status.",
            "instructions": """You are coder_01.
Implement and explain code-level tasks assigned by the Planner.
If you need clarification, ask the Planner. Provide progress updates for the Manager when appropriate.
Always respond with JSON containing messages and notes.
""",
            "config": {
                "model": "gpt-4.1",
                "org_speed_multiplier": 1,
                "send_to": ["planner", "manager"],
                "read_from": ["planner"],
                "max_credits": 200.0,
                "priority": "high",
            },
        },
        "janitor": {
            "role": "Cleanup and maintenance",
            "description": "Janitor suggests cleanup of expired or excessive messages and files.",
            "instructions": """You are the Janitor agent.
Inspect the organization for stale or excessive messages and propose cleanup actions.
You cannot delete files directly; request actions via messages to the Manager.
Always respond with JSON containing messages and notes.
""",
            "config": {
                "model": "gpt-4.1-mini",
                "org_speed_multiplier": 3,
                "send_to": ["manager"],
                "read_from": ["manager", "planner", "coder_01", "hr"],
                "max_credits": 50.0,
                "priority": "normal",
            },
        },
    }

    for name, info in agent_defs.items():
        agent_dir = base_path / "agents" / name
        ensure_agent_dirs(agent_dir)
        resume_path = agent_dir / "resume.txt"
        if not resume_path.exists():
            write_resume(
                resume_path,
                name=info.get("name", name).upper(),
                role=info["role"],
                description=info["description"],
                instructions=info["instructions"],
                config=info["config"],
            )
            logger.info("Created resume for %s", name)

    reset_caches()


def main() -> None:
    parser = argparse.ArgumentParser(description="LeMMing CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("bootstrap", help="Bootstrap default configs and agents")
    sub.add_parser("run", help="Run the engine indefinitely")
    sub.add_parser("run-once", help="Run a single engine turn")

    args = parser.parse_args()
    base_path = Path(__file__).resolve().parent.parent

    if args.command == "bootstrap":
        bootstrap(base_path)
    elif args.command == "run":
        run_forever(base_path)
    elif args.command == "run-once":
        run_once(base_path, current_turn=1)


if __name__ == "__main__":
    main()
