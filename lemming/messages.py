from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OutboxEntry:
    id: str
    timestamp: str
    tick: int
    agent: str
    kind: str
    payload: dict[str, Any]
    tags: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        agent: str,
        tick: int,
        kind: str,
        payload: dict[str, Any],
        tags: list[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> OutboxEntry:
        timestamp = datetime.now(UTC).isoformat()
        entry_id = f"msg_{timestamp}_{uuid.uuid4().hex[:8]}"
        return cls(
            id=entry_id,
            timestamp=timestamp,
            tick=tick,
            agent=agent,
            kind=kind,
            payload=payload,
            tags=tags or [],
            meta=meta or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OutboxEntry:
        return cls(**data)


def write_outbox_entry(base_path: Path, agent_name: str, entry: OutboxEntry) -> Path:
    outbox_dir = base_path / "agents" / agent_name / "outbox"
    outbox_dir.mkdir(parents=True, exist_ok=True)
    entry_path = outbox_dir / f"{entry.id}.json"
    with entry_path.open("w", encoding="utf-8") as f:
        json.dump(entry.to_dict(), f, indent=2)
    return entry_path


def read_outbox_entries(
    base_path: Path, agent_name: str, limit: int = 50, since_tick: int | None = None
) -> list[OutboxEntry]:
    outbox_dir = base_path / "agents" / agent_name / "outbox"
    if not outbox_dir.exists():
        return []

    entries: list[OutboxEntry] = []
    for entry_path in outbox_dir.glob("msg_*.json"):
        try:
            with entry_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            entry = OutboxEntry.from_dict(data)
            if since_tick is not None and entry.tick < since_tick:
                continue
            entries.append(entry)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to read outbox entry %s: %s", entry_path, exc)

    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return entries[:limit]


def collect_readable_outboxes(
    base_path: Path,
    agent_name: str,
    read_outboxes: list[str],
    limit: int = 50,
    since_tick: int | None = None,
) -> list[OutboxEntry]:
    entries: list[OutboxEntry] = []
    if read_outboxes == ["*"]:
        agents_dir = base_path / "agents"
        if agents_dir.exists():
            read_outboxes = [
                d.name for d in agents_dir.iterdir() if d.is_dir() and d.name not in {agent_name, "agent_template"}
            ]
    for other in read_outboxes:
        if other == agent_name:
            continue
        entries.extend(read_outbox_entries(base_path, other, limit=limit, since_tick=since_tick))
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return entries[:limit]


def cleanup_old_outbox_entries(base_path: Path, current_tick: int, max_age_ticks: int = 100) -> int:
    removed = 0
    agents_dir = base_path / "agents"
    if not agents_dir.exists():
        return 0

    for agent_dir in agents_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        outbox_dir = agent_dir / "outbox"
        if not outbox_dir.exists():
            continue
        for entry_path in outbox_dir.glob("msg_*.json"):
            try:
                with entry_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                tick = int(data.get("tick", 0))
                if current_tick - tick > max_age_ticks:
                    entry_path.unlink()
                    removed += 1
            except Exception as exc:  # pragma: no cover
                logger.error("Failed to clean outbox entry %s: %s", entry_path, exc)
    return removed


def format_outbox_context(entries: list[OutboxEntry], max_chars: int = 8000) -> str:
    if not entries:
        return "No incoming messages."

    lines = ["INCOMING MESSAGES:"]
    total = len(lines[0])
    for entry in entries:
        text = entry.payload.get("text", json.dumps(entry.payload))
        line = f"\n[{entry.timestamp}] From {entry.agent} ({entry.kind}): {text}"
        if total + len(line) > max_chars:
            lines.append("\n... (truncated)")
            break
        lines.append(line)
        total += len(line)
    return "".join(lines)
