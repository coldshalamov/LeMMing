"""Agent memory management system."""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .paths import get_memory_dir

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
    memory_dir = get_memory_dir(base_path, agent_name)
    memory_dir.mkdir(parents=True, exist_ok=True)

    memory_file = memory_dir / f"{key}.json"
    entry = {"key": key, "value": value, "timestamp": datetime.now(UTC).isoformat(), "agent": agent_name}

    with memory_file.open("w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2)

    logger.debug(
        "memory_saved",
        extra={"event": "memory_saved", "agent": agent_name, "key": key},
    )


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
    memory_file = get_memory_dir(base_path, agent_name) / f"{key}.json"

    if not memory_file.exists():
        return None

    try:
        with memory_file.open("r", encoding="utf-8") as f:
            entry = json.load(f)
        return entry.get("value")
    except Exception as exc:
        logger.error(
            "memory_load_failed",
            extra={
                "event": "memory_load_failed",
                "agent": agent_name,
                "key": key,
                "error": str(exc),
            },
        )
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
    memory_dir = get_memory_dir(base_path, agent_name)

    if not memory_dir.exists():
        return []

    # Optimization: Use os.scandir to avoid creating Path objects
    try:
        with os.scandir(memory_dir) as it:
            return [
                entry.name[:-5]  # Faster than partition or split for known suffix
                for entry in it
                if entry.is_file() and entry.name.endswith(".json")
            ]
    except FileNotFoundError:
        return []


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
    memory_file = get_memory_dir(base_path, agent_name) / f"{key}.json"

    if not memory_file.exists():
        return False

    memory_file.unlink()
    logger.info(
        "memory_deleted",
        extra={"event": "memory_deleted", "agent": agent_name, "key": key},
    )
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


def append_memory_event(
    base_path: Path,
    agent_name: str,
    key: str,
    event: str,
    *,
    max_entries: int | None = 100,
) -> None:
    """
    Append a timestamped event to a list-based memory entry.

    Args:
        base_path: Base path of the LeMMing installation
        agent_name: Name of the agent
        key: Memory key (list of event dicts)
        event: Event description or payload
        max_entries: Optional cap to keep only the most recent entries
    """

    entry = {"timestamp": datetime.now(UTC).isoformat(), "event": event}
    current = load_memory(base_path, agent_name, key)

    if current is None:
        current = []
    elif not isinstance(current, list):
        raise ValueError(f"Memory key '{key}' is not a list")

    current.append(entry)
    if max_entries and len(current) > max_entries:
        current = current[-max_entries:]

    save_memory(base_path, agent_name, key, current)


def load_recent_memory_events(base_path: Path, agent_name: str, key: str, limit: int = 5) -> list[dict[str, Any]]:
    """Load up to ``limit`` most recent events from a list-based memory key."""

    events = load_memory(base_path, agent_name, key)
    if events is None:
        return []
    if not isinstance(events, list):
        raise ValueError(f"Memory key '{key}' is not a list")

    return events[-limit:]


def summarize_memory_events(base_path: Path, agent_name: str, key: str, limit: int = 5) -> str:
    """
    Provide a short, human-readable summary of recent events for an agent.
    """

    recent = load_recent_memory_events(base_path, agent_name, key, limit=limit)
    if not recent:
        return "No recorded events."

    lines = [f"- {item['timestamp']}: {item['event']}" for item in recent if "event" in item and "timestamp" in item]
    return "\n".join(lines)


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


def get_memory_context(base_path: Path, agent_name: str, max_items: int = 20) -> str:
    """
    Return a text block summarizing the agent's memory suitable for prompt injection.
    May truncate or summarize if there are many keys/values.
    """

    summary = get_memory_summary(base_path, agent_name)
    if not summary:
        return "No memory entries."

    lines: list[str] = []
    for idx, (key, value) in enumerate(summary.items()):
        if idx >= max_items:
            lines.append("... (truncated)")
            break
        display = value
        try:
            display = json.dumps(value)
        except Exception:  # pragma: no cover - best effort
            display = str(value)
        lines.append(f"{key}: {display}")
    return "\n".join(lines)


def compact_memory_list(
    base_path: Path,
    agent_name: str,
    key: str,
    max_entries: int = 100,
) -> int:
    """Compact a list-based memory entry by keeping only the most recent entries.

    Args:
        base_path: Base path of the LeMMing installation
        agent_name: Name of the agent
        key: Memory key (must be a list)
        max_entries: Maximum number of entries to keep

    Returns:
        Number of entries removed
    """
    current = load_memory(base_path, agent_name, key)

    if current is None:
        return 0
    if not isinstance(current, list):
        logger.warning(
            "memory_compact_skipped",
            extra={
                "event": "memory_compact_skipped",
                "agent": agent_name,
                "key": key,
            },
        )
        return 0

    original_count = len(current)
    if original_count <= max_entries:
        return 0

    # Keep only the most recent entries
    compacted = current[-max_entries:]
    save_memory(base_path, agent_name, key, compacted)

    removed = original_count - len(compacted)
    logger.info(
        "memory_compacted",
        extra={
            "event": "memory_compacted",
            "agent": agent_name,
            "key": key,
            "removed": removed,
        },
    )
    return removed


def archive_old_memories(
    base_path: Path,
    agent_name: str,
    days_old: int = 30,
) -> int:
    """Archive memory files older than a specified number of days.

    Moves old memory files to an archive subdirectory.

    Args:
        base_path: Base path of the LeMMing installation
        agent_name: Name of the agent
        days_old: Archive memories older than this many days

    Returns:
        Number of memories archived
    """
    memory_dir = get_memory_dir(base_path, agent_name)
    if not memory_dir.exists():
        return 0

    archive_dir = memory_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    cutoff_time = datetime.now(UTC) - timedelta(days=days_old)
    archived_count = 0

    try:
        with os.scandir(memory_dir) as it:
            for entry in it:
                if not entry.is_file() or not entry.name.endswith(".json"):
                    continue

                try:
                    with open(entry.path, encoding="utf-8") as f:
                        data = json.load(f)

                    timestamp_str = data.get("timestamp")
                    if not timestamp_str:
                        continue

                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp < cutoff_time:
                        # Move to archive
                        archive_path = archive_dir / entry.name
                        shutil.move(entry.path, str(archive_path))
                        archived_count += 1
                        logger.info(
                            "memory_archived",
                            extra={
                                "event": "memory_archived",
                                "agent": agent_name,
                                "key": entry.name[:-5],
                            },
                        )

                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning(
                        "memory_archive_failed",
                        extra={
                            "event": "memory_archive_failed",
                            "agent": agent_name,
                            "key": entry.name[:-5],
                            "error": str(exc),
                        },
                    )
    except FileNotFoundError:
        pass

    return archived_count


def compact_all_agent_memories(
    base_path: Path,
    agent_name: str,
    max_entries: int = 100,
) -> dict[str, int]:
    """Compact all list-based memories for an agent.

    Args:
        base_path: Base path of the LeMMing installation
        agent_name: Name of the agent
        max_entries: Maximum entries to keep per memory key

    Returns:
        Dictionary mapping memory keys to number of entries removed
    """
    keys = list_memories(base_path, agent_name)
    results = {}

    for key in keys:
        removed = compact_memory_list(base_path, agent_name, key, max_entries)
        if removed > 0:
            results[key] = removed

    return results
