"""Centralized filesystem path helpers for LeMMing."""

import re
from pathlib import Path


def validate_agent_name(name: str) -> None:
    """Validate that the agent name is safe to use in paths."""
    if not name:
        raise ValueError("Agent name cannot be empty")

    # Strict allowlist: alphanumeric, underscores, hyphens
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValueError(
            f"Agent name '{name}' is invalid. Only alphanumeric characters, " "underscores, and hyphens are allowed."
            f"Agent name '{name}' is invalid. Only alphanumeric characters, underscores, and hyphens are allowed."
        )


def get_config_dir(base_path: Path) -> Path:
    return base_path / "lemming" / "config"


def get_agents_dir(base_path: Path) -> Path:
    return base_path / "agents"


def get_agent_dir(base_path: Path, agent_name: str) -> Path:
    validate_agent_name(agent_name)
    return get_agents_dir(base_path) / agent_name


def get_resume_json_path(base_path: Path, agent_name: str) -> Path:
    return get_agent_dir(base_path, agent_name) / "resume.json"


def get_resume_txt_path(base_path: Path, agent_name: str) -> Path:
    return get_agent_dir(base_path, agent_name) / "resume.txt"


def get_outbox_dir(base_path: Path, agent_name: str) -> Path:
    return get_agent_dir(base_path, agent_name) / "outbox"


def get_memory_dir(base_path: Path, agent_name: str) -> Path:
    return get_agent_dir(base_path, agent_name) / "memory"


def get_logs_dir(base_path: Path, agent_name: str) -> Path:
    return get_agent_dir(base_path, agent_name) / "logs"


def get_tick_file(base_path: Path) -> Path:
    return get_config_dir(base_path) / "tick.json"
