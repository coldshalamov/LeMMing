from __future__ import annotations

"""Bootstrap utilities for preparing a LeMMing workspace.

The helpers here are intentionally conservative: they only create missing files
or directories and never overwrite user edits.
"""

import json
import shutil
from pathlib import Path
from typing import Any

from .agents import DEFAULT_CREDITS, discover_agents
from .paths import get_agents_dir, get_config_dir


def _copy_if_missing(src: Path, dest: Path) -> bool:
    if dest.exists():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True


def ensure_config_files(base_path: Path) -> list[str]:
    """Ensure config JSON files exist under ``lemming/config``.

    Returns a list of filenames that were created.
    """

    created: list[str] = []
    config_dir = get_config_dir(base_path)
    default_config_dir = Path(__file__).parent / "config"

    for json_file in default_config_dir.glob("*.json"):
        dest = config_dir / json_file.name
        if _copy_if_missing(json_file, dest):
            created.append(json_file.name)
    return created


def ensure_agent_template(base_path: Path) -> bool:
    """Copy the agent template into the workspace if missing."""

    target_dir = get_agents_dir(base_path) / "agent_template"
    if target_dir.exists():
        return False

    source_dir = Path(__file__).resolve().parent.parent / "agents" / "agent_template"
    if not source_dir.exists():
        raise FileNotFoundError("Default agent template is missing from the package")

    shutil.copytree(source_dir, target_dir)
    return True


def create_example_agent(base_path: Path) -> bool:
    """Create a simple example agent if none exist yet."""

    agents_dir = get_agents_dir(base_path)
    agents_dir.mkdir(parents=True, exist_ok=True)

    existing = [d for d in agents_dir.iterdir() if d.is_dir() and d.name != "agent_template"]
    if existing:
        return False

    example_dir = agents_dir / "example_planner"
    example_dir.mkdir(parents=True, exist_ok=True)

    resume = {
        "name": "example_planner",
        "title": "Example planning agent",
        "short_description": "Creates a simple plan each tick.",
        "workflow_description": "Drafts a short TODO list and updates its memory.",
        "model": {"key": "gpt-4.1-mini", "temperature": 0.2, "max_tokens": 1024},
        "permissions": {"read_outboxes": [], "tools": ["memory_read", "memory_write"]},
        "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},
        "credits": DEFAULT_CREDITS,
        "instructions": (
            "Review any recent messages, produce a concise TODO list, and store it in memory. "
            "If there is nothing to do, note that gracefully."
        ),
    }

    resume_path = example_dir / "resume.json"
    with resume_path.open("w", encoding="utf-8") as f:
        json.dump(resume, f, indent=2)

    return True


def ensure_logs_dir(base_path: Path) -> bool:
    """Ensure the top-level logs directory exists."""

    logs_dir = base_path / "logs"
    if logs_dir.exists():
        return False
    logs_dir.mkdir(parents=True, exist_ok=True)
    return True


def bootstrap(base_path: Path) -> dict[str, Any]:
    """Perform all bootstrap steps in an idempotent manner."""

    created_configs = ensure_config_files(base_path)
    template_created = ensure_agent_template(base_path)
    example_created = create_example_agent(base_path)
    logs_created = ensure_logs_dir(base_path)

    # Touch credits to ensure entries exist for any agents present.
    agents = discover_agents(base_path)
    if agents:
        config_dir = get_config_dir(base_path)
        credits_path = config_dir / "credits.json"
        try:
            credits = json.loads(credits_path.read_text(encoding="utf-8"))
        except Exception:
            credits = {}
        updated = False
        for agent in agents:
            if agent.name not in credits:
                credits[agent.name] = {
                    "model": agent.model.key,
                    "cost_per_action": 0.01,
                    "credits_left": agent.credits.max_credits,
                }
                updated = True
        if updated:
            credits_path.parent.mkdir(parents=True, exist_ok=True)
            credits_path.write_text(json.dumps(credits, indent=2), encoding="utf-8")

    return {
        "created_configs": created_configs,
        "template_created": template_created,
        "example_created": example_created,
        "logs_dir_created": logs_created,
    }
