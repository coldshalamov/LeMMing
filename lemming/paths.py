"""Centralized filesystem path helpers for LeMMing."""

import os
import re
from pathlib import Path


def validate_agent_name(agent_name: str) -> None:
    """Validates that the agent name is safe to use in file paths.

    Raises:
        ValueError: If the agent name contains invalid characters or path traversal components.
    """
    if not agent_name:
        raise ValueError("Agent name cannot be empty")

    # Check for path separators and traversal components explicitly for better error messages
    if "/" in agent_name or "\\" in agent_name:
        raise ValueError(f"Agent name '{agent_name}' contains path separators")

    if agent_name in {".", ".."}:
        raise ValueError(f"Agent name '{agent_name}' is invalid")

    # Enforce safe characters: alphanumeric, underscore, hyphen
    if not re.match(r"^[a-zA-Z0-9_-]+$", agent_name):
        raise ValueError(f"Agent name '{agent_name}' contains invalid characters. Allowed: a-z, A-Z, 0-9, _, -")


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
