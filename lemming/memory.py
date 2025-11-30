"""Agent memory management system."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def save_memory(base_path: Path, agent_name: str, key: str, value: Any) -> None:
    """
    Save a memory entry for an agent.

    Args:
        base_path: Base path of the LeMMing installation
        agent_name: Name of the agent
        key: Memory key (e.g., "context", "facts", "goals")
        value: Value to store (will be JSON serialized)
    """
    memory_dir = base_path / "agents" / agent_name / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)

    memory_file = memory_dir / f"{key}.json"
    entry = {"key": key, "value": value, "timestamp": datetime.now(timezone.utc).isoformat(), "agent": agent_name}

    with memory_file.open("w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2)

    logger.debug("Saved memory for %s: %s", agent_name, key)


def load_memory(base_path: Path, agent_name: str, key: str) -> Any | None:
    """
    Load a memory entry for an agent.

    Args:
        base_path: Base path of the LeMMing installation
        agent_name: Name of the agent
        key: Memory key to load

    Returns:
        The stored value, or None if not found
    """
    memory_file = base_path / "agents" / agent_name / "memory" / f"{key}.json"

    if not memory_file.exists():
        return None

    try:
        with memory_file.open("r", encoding="utf-8") as f:
            entry = json.load(f)
        return entry.get("value")
    except Exception as exc:
        logger.error("Failed to load memory for %s/%s: %s", agent_name, key, exc)
        return None


def list_memories(base_path: Path, agent_name: str) -> list[str]:
    """
    List all memory keys for an agent.

    Args:
        base_path: Base path of the LeMMing installation
        agent_name: Name of the agent

    Returns:
        List of memory keys
    """
    memory_dir = base_path / "agents" / agent_name / "memory"

    if not memory_dir.exists():
        return []

    return [f.stem for f in memory_dir.glob("*.json")]


def delete_memory(base_path: Path, agent_name: str, key: str) -> bool:
    """
    Delete a memory entry for an agent.

    Args:
        base_path: Base path of the LeMMing installation
        agent_name: Name of the agent
        key: Memory key to delete

    Returns:
        True if deleted, False if not found
    """
    memory_file = base_path / "agents" / agent_name / "memory" / f"{key}.json"

    if not memory_file.exists():
        return False

    memory_file.unlink()
    logger.info("Deleted memory for %s: %s", agent_name, key)
    return True


def append_to_memory_list(base_path: Path, agent_name: str, key: str, item: Any) -> None:
    """
    Append an item to a list-based memory.

    Args:
        base_path: Base path of the LeMMing installation
        agent_name: Name of the agent
        key: Memory key (must be a list)
        item: Item to append
    """
    current = load_memory(base_path, agent_name, key)

    if current is None:
        current = []
    elif not isinstance(current, list):
        raise ValueError(f"Memory key '{key}' is not a list")

    current.append(item)
    save_memory(base_path, agent_name, key, current)


def get_memory_summary(base_path: Path, agent_name: str) -> dict[str, Any]:
    """
    Get a summary of all memories for an agent.

    Args:
        base_path: Base path of the LeMMing installation
        agent_name: Name of the agent

    Returns:
        Dictionary mapping keys to values
    """
    keys = list_memories(base_path, agent_name)
    summary = {}

    for key in keys:
        summary[key] = load_memory(base_path, agent_name, key)

    return summary
