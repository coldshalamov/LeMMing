from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
import os
from typing import Any

from .paths import get_agents_dir, get_outbox_dir

logger = logging.getLogger(__name__)


OUTBOX_FILENAME_TEMPLATE = "{tick:08d}_{entry_id}.json"


@dataclass
class OutboxEntry:
    """Canonical outbox message entry.

    ``meta`` is retained for backward compatibility with existing callers but is
    not part of the core ABI fields.
    """

    id: str
    tick: int
    agent: str
    kind: str
    payload: dict[str, Any]
    tags: list[str]
    created_at: str
    recipients: list[str] | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        agent: str,
        tick: int,
        kind: str,
        payload: dict[str, Any],
        tags: list[str] | None = None,
        recipients: list[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> OutboxEntry:
        created_at = datetime.now(UTC).isoformat()
        entry_id = uuid.uuid4().hex
        return cls(
            id=entry_id,
            tick=tick,
            agent=agent,
            kind=kind,
            payload=payload,
            tags=tags or [],
            created_at=created_at,
            recipients=recipients,
            meta=meta or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OutboxEntry:
        # Backward compatibility: older entries used ``timestamp``.
        if "created_at" not in data and "timestamp" in data:
            data = dict(data)
            data["created_at"] = data.pop("timestamp")
        if "recipients" not in data:
            data = dict(data)
            data["recipients"] = None
        return cls(**data)


def outbox_filename(entry: OutboxEntry) -> str:
    return OUTBOX_FILENAME_TEMPLATE.format(tick=entry.tick, entry_id=entry.id)


def write_outbox_entry(base_path: Path, agent_name: str, entry: OutboxEntry) -> Path:
    outbox_dir = get_outbox_dir(base_path, agent_name)
    outbox_dir.mkdir(parents=True, exist_ok=True)
    entry_path = outbox_dir / outbox_filename(entry)
    with entry_path.open("w", encoding="utf-8") as f:
        json.dump(entry.to_dict(), f, indent=2)
    return entry_path


def _load_entry(entry_path: Path) -> OutboxEntry | None:
    try:
        with entry_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return OutboxEntry.from_dict(data)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(
            "outbox_read_failed",
            extra={
                "event": "outbox_read_failed",
                "path": str(entry_path),
                "error": str(exc),
            },
        )
        return None


def _tick_from_filename(entry_path: Path) -> int | None:
    try:
        stem = entry_path.stem
        tick_part = stem.split("_", 1)[0]
        return int(tick_part)
    except Exception:
        return None


def _outbox_sort_key(p: Path) -> tuple[int, str]:
    """Helper to sort outbox files by tick first, then filename.

    Returns (tick, filename). If tick cannot be parsed, returns (-1, filename)
    so these files appear at the end (or beginning, depending on sort order).
    """
    tick = _tick_from_filename(p)
    return (tick if tick is not None else -1, p.name)


def read_outbox_entries(
    base_path: Path, agent_name: str, limit: int = 50, since_tick: int | None = None
) -> list[OutboxEntry]:
    outbox_dir = get_outbox_dir(base_path, agent_name)
    if not outbox_dir.exists():
        return []

    if limit <= 0:
        return []

    entries: list[OutboxEntry] = []

    # Sort files by tick descending.
    # We use a custom key to extract the tick from the filename, ensuring numerical sort.
    # This allows us to stop reading files once we have enough entries from
    # recent ticks, avoiding reading the entire history.
    files = sorted(outbox_dir.glob("*.json"), key=_outbox_sort_key, reverse=True)

    min_collected_tick = float('inf')

    for entry_path in files:
        tick_val = _tick_from_filename(entry_path)

        # If we encounter a file with a tick older than since_tick, we can stop
        # because subsequent files (sorted by tick desc) will have even smaller ticks.
        # We only break if tick_val is valid (not None).
        if since_tick is not None:
            if tick_val is not None and tick_val < since_tick:
                break

        # Optimization: If we have collected enough entries, check if we can stop.
        if len(entries) >= limit:
            # We have at least 'limit' entries.
            # We maintain min_collected_tick as we go.
            # If the current file's tick is strictly less than the minimum tick
            # we have already accepted, then this file (and all subsequent ones)
            # are definitely older than what we have, so we can stop.
            if tick_val is not None and min_collected_tick > tick_val:
                break

        entry = _load_entry(entry_path)
        if entry is None:
            continue

        # Still need to check since_tick in case filename parsing failed or logic differed
        if since_tick is not None and entry.tick < since_tick:
            continue

        entries.append(entry)

        if entry.tick < min_collected_tick:
            min_collected_tick = entry.tick

    entries.sort(key=lambda e: (e.tick, e.created_at), reverse=True)
    return entries[:limit]


def count_outbox_entries(base_path: Path, agent_name: str) -> int:
    """Efficiently count the number of outbox entries for an agent.

    This avoids reading and parsing the JSON files, which is significantly faster.
    """
    outbox_dir = get_outbox_dir(base_path, agent_name)
    if not outbox_dir.exists():
        return 0

    try:
        count = 0
        with os.scandir(outbox_dir) as it:
            for entry in it:
                if entry.name.endswith(".json") and entry.is_file():
                    count += 1
        return count
    except FileNotFoundError:
        return 0


def collect_readable_outboxes(
    base_path: Path,
    agent_name: str,
    read_outboxes: list[str],
    limit: int = 50,
    since_tick: int | None = None,
) -> list[OutboxEntry]:
    entries: list[OutboxEntry] = []
    if read_outboxes == ["*"]:
        agents_dir = get_agents_dir(base_path)
        if agents_dir.exists():
            read_outboxes = [
                d.name
                for d in agents_dir.iterdir()
                if d.is_dir() and d.name not in {agent_name, "agent_template"}
            ]
    for other in read_outboxes:
        if other == agent_name:
            continue
        entries.extend(read_outbox_entries(base_path, other, limit=limit, since_tick=since_tick))
    entries.sort(key=lambda e: (e.tick, e.created_at), reverse=True)
    return entries[:limit]


def cleanup_old_outbox_entries(base_path: Path, current_tick: int, max_age_ticks: int = 100) -> int:
    removed = 0
    agents_dir = get_agents_dir(base_path)
    if not agents_dir.exists():
        return 0

    for agent_dir in agents_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        outbox_dir = get_outbox_dir(base_path, agent_dir.name)
        if not outbox_dir.exists():
            continue
        for entry_path in outbox_dir.glob("*.json"):
            tick_val = _tick_from_filename(entry_path)
            if tick_val is None:
                continue
            if current_tick - tick_val > max_age_ticks:
                try:
                    entry_path.unlink()
                    removed += 1
                except Exception as exc:  # pragma: no cover
                    logger.error(
                        "outbox_cleanup_failed",
                        extra={
                            "event": "outbox_cleanup_failed",
                            "path": str(entry_path),
                            "error": str(exc),
                        },
                    )
    return removed


def format_outbox_context(entries: list[OutboxEntry], max_chars: int = 8000) -> str:
    if not entries:
        return "No incoming messages."

    lines = ["INCOMING MESSAGES:"]
    total = len(lines[0])
    for entry in entries:
        text = entry.payload.get("text", json.dumps(entry.payload))
        line = f"\n[{entry.created_at}] From {entry.agent} ({entry.kind}): {text}"
        if total + len(line) > max_chars:
            lines.append("\n... (truncated)")
            break
        lines.append(line)
        total += len(line)
    return "".join(lines)
