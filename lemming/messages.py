from __future__ import annotations

import heapq
import itertools
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .paths import get_agents_dir, get_outbox_dir

logger = logging.getLogger(__name__)


OUTBOX_FILENAME_TEMPLATE = "{tick:08d}_{entry_id}.json"

# Caches for outbox operations to avoid repetitive filesystem scans
# Key: outbox_dir_path -> (mtime, count)
_outbox_count_cache: dict[Path, tuple[float, int]] = {}
# Key: outbox_dir_path -> (mtime, list_of_filenames_sorted_desc)
_outbox_files_cache: dict[Path, tuple[float, list[str]]] = {}


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
        # Optimization: Manual dict construction is ~30x faster than dataclasses.asdict
        # because it avoids deep recursive copying and inspection overhead.
        # We perform shallow copies of mutable fields to preserve basic safety.
        return {
            "id": self.id,
            "tick": self.tick,
            "agent": self.agent,
            "kind": self.kind,
            "payload": self.payload.copy(),
            "tags": self.tags[:],
            "created_at": self.created_at,
            "recipients": self.recipients[:] if self.recipients is not None else None,
            "meta": self.meta.copy(),
        }

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
    # Optimization: removed outbox_dir.mkdir call to rely on try/except block below
    # which saves a syscall.

    entry_path = outbox_dir / outbox_filename(entry)

    try:
        with entry_path.open("w", encoding="utf-8") as f:
            json.dump(entry.to_dict(), f, indent=2)
    except FileNotFoundError:
        # Parent directory likely doesn't exist
        outbox_dir.mkdir(parents=True, exist_ok=True)
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
        # Optimization: Use .name instead of .stem to avoid property overhead,
        # and partition which is faster than split.
        tick_part = entry_path.name.partition("_")[0]
        return int(tick_part)
    except Exception:
        return None


def _tick_from_filename_str(filename: str) -> int:
    """Helper to extract tick from filename string.

    Returns -1 if parsing fails so it sorts to the end.
    """
    try:
        # Optimization: partition is faster than split
        tick_part = filename.partition("_")[0]
        return int(tick_part)
    except (ValueError, IndexError):
        return -1


def scan_outbox_files(
    base_path: Path, agent_name: str, since_tick: int | None = None, limit: int = 0
) -> list[tuple[int, str]]:
    """Scans outbox files and returns list of (tick, filename) without loading content.

    This is faster than read_outbox_entries when we only need to sort by tick/filename
    across multiple agents.

    If limit > 0, returns only the most recent 'limit' entries using heapq.
    """
    return [
        (tick, filename) for tick, filename, _ in _scan_outbox_files_optimized(base_path, agent_name, since_tick, limit)
    ]


def _scan_outbox_files_optimized(
    base_path: Path, agent_name: str, since_tick: int | None = None, limit: int = 0
) -> list[tuple[int, str, str]]:
    """Internal optimized version returning (tick, filename, full_path_str)."""
    outbox_dir = get_outbox_dir(base_path, agent_name)
    results = []

    try:
        # Optimization: Use st_mtime as cache key. Directory mtime updates when files are added/removed.
        # This replaces O(N) scan with O(1) cache lookup for repeated calls.
        mtime = outbox_dir.stat().st_mtime

        cached = _outbox_files_cache.get(outbox_dir)
        if cached and cached[0] == mtime:
            filenames = cached[1]
        else:
            # Cache miss or stale: scan all files
            with os.scandir(outbox_dir) as it:
                filenames = sorted(
                    (
                        entry.name
                        for entry in it
                        if entry.is_file() and entry.name.endswith(".json") and entry.name[0].isdigit()
                    ),
                    reverse=True,
                )

            # Simple eviction policy to prevent memory leaks
            if len(_outbox_files_cache) > 1000:
                _outbox_files_cache.clear()

            _outbox_files_cache[outbox_dir] = (mtime, filenames)

        outbox_dir_str = str(outbox_dir)

        # Apply filters to cached list
        count = 0
        for name in filenames:
            tick = _tick_from_filename_str(name)
            if tick == -1:
                continue

            if since_tick is not None and tick < since_tick:
                # Since list is sorted descending, we can stop early if looking for > since_tick
                # Wait, "since_tick" means we want entries with tick >= since_tick.
                # If current tick < since_tick, then all subsequent ticks are also smaller.
                break

            full_path = os.path.join(outbox_dir_str, name)
            results.append((tick, name, full_path))

            count += 1
            if limit > 0 and count >= limit:
                break

    except FileNotFoundError:
        pass

    return results


def read_outbox_entries(
    base_path: Path, agent_name: str, limit: int = 50, since_tick: int | None = None
) -> list[OutboxEntry]:
    outbox_dir = get_outbox_dir(base_path, agent_name)
    # Optimization: removed outbox_dir.exists() check to rely on try/except block below

    if limit <= 0:
        return []

    entries: list[OutboxEntry] = []

    # Sort files by tick descending.
    # Optimization: Use os.scandir to avoid creating Path objects for all files.
    # Use heapq.nlargest to avoid sorting all files when we only need the top K.
    try:
        with os.scandir(outbox_dir) as it:
            # Helper generator to filter non-json files
            candidate_files = (entry.name for entry in it if entry.is_file() and entry.name.endswith(".json"))

            # If since_tick is provided, we can pre-filter files that are definitely too old
            # IF the filename tick parsing is reliable. It is.
            if since_tick is not None:
                candidate_files = (name for name in candidate_files if _tick_from_filename_str(name) >= since_tick)

            filenames = heapq.nlargest(limit, candidate_files, key=None)
    except FileNotFoundError:
        return []

    min_collected_tick = float("inf")

    for name in filenames:
        # Optimization: Parse tick from filename string directly to avoid Path creation.
        # _tick_from_filename_str returns -1 on error.
        tick_val_int = _tick_from_filename_str(name)
        tick_val = tick_val_int if tick_val_int != -1 else None

        # If we encounter a file with a tick older than since_tick, we can stop
        # because subsequent files (sorted by tick desc) will have even smaller ticks.
        # We only break if tick_val is valid (not None).
        if since_tick is not None:
            if tick_val is not None and tick_val < since_tick:
                break

        # Optimization: If we have collected enough entries, check if we can stop.
        if len(entries) >= limit:
            if tick_val is not None and min_collected_tick > tick_val:
                break

        entry_path = outbox_dir / name
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

    try:
        # Optimization: Check cache first based on directory mtime
        mtime = outbox_dir.stat().st_mtime

        cached = _outbox_count_cache.get(outbox_dir)
        if cached and cached[0] == mtime:
            return cached[1]

        count = 0
        with os.scandir(outbox_dir) as it:
            for entry in it:
                if entry.name.endswith(".json") and entry.is_file():
                    count += 1

        # Simple eviction policy to prevent memory leaks
        if len(_outbox_count_cache) > 1000:
            _outbox_count_cache.clear()

        _outbox_count_cache[outbox_dir] = (mtime, count)
        return count
    except FileNotFoundError:
        return 0


def read_multi_agent_outbox_entries(
    base_path: Path, agent_names: list[str], limit: int = 50, since_tick: int | None = None
) -> list[OutboxEntry]:
    """Efficiently read outbox entries across multiple agents.

    This avoids loading 'limit' entries for *each* agent and then sorting them.
    Instead, it scans metadata (filenames) from all agents, merges the sorted streams,
    picks the top 'limit' candidates globally, and ONLY loads those files.
    """
    if limit <= 0:
        return []

    # 1. Gather sorted metadata streams from all agents
    iterables = []
    for agent_name in agent_names:
        iterables.append(_scan_outbox_files_optimized(base_path, agent_name, since_tick=since_tick, limit=limit))

    # 2. Merge sorted streams to find global top candidates
    # _scan_outbox_files_optimized returns (tick, filename, full_path) sorted descending by tick.
    # Optimization: (tick, filename, path) tuple comparison is sufficient
    # and equivalent to (tick, filename) since filename implies tick and is unique per agent.
    merged = heapq.merge(*iterables, reverse=True)

    # 3. Take top 'limit' candidates
    to_load = list(itertools.islice(merged, limit))

    # 4. Load only the necessary files
    entries: list[OutboxEntry] = []
    for _, _, path_str in to_load:
        entry = _load_entry(Path(path_str))
        if entry is None:
            continue
        entries.append(entry)

    # 5. Final sort (just in case created_at differs for same tick, or to be safe)
    entries.sort(key=lambda e: (e.tick, e.created_at), reverse=True)
    return entries


def collect_readable_outboxes(
    base_path: Path,
    agent_name: str,
    read_outboxes: list[str],
    limit: int = 50,
    since_tick: int | None = None,
) -> list[OutboxEntry]:
    if read_outboxes == ["*"]:
        agents_dir = get_agents_dir(base_path)
        if not agents_dir.exists():
            return []
        # Optimization: Use os.scandir to avoid creating Path objects
        with os.scandir(agents_dir) as it:
            read_outboxes = [
                entry.name for entry in it if entry.is_dir() and entry.name not in {agent_name, "agent_template"}
            ]
    else:
        # Filter out self if present
        read_outboxes = [name for name in read_outboxes if name != agent_name]

    return read_multi_agent_outbox_entries(base_path, read_outboxes, limit=limit, since_tick=since_tick)


def cleanup_old_outbox_entries(base_path: Path, current_tick: int, max_age_ticks: int = 100) -> int:
    removed = 0
    agents_dir = get_agents_dir(base_path)
    # Optimization: Removed agents_dir.exists() check to rely on try/except block below

    # Optimization: Use os.scandir to iterate agents efficiently
    try:
        with os.scandir(agents_dir) as it:
            for agent_entry in it:
                if not agent_entry.is_dir():
                    continue

                # Optimization: Construct path manually to avoid get_outbox_dir overhead
                # (validation + Path creation). Structure: agents_dir / agent_name / "outbox"
                # agent_entry.path is the full path to the agent dir.
                outbox_dir_str = os.path.join(agent_entry.path, "outbox")

                # Optimization: Removed outbox_dir.exists() check to rely on try/except block

                try:
                    with os.scandir(outbox_dir_str) as outbox_it:
                        for entry in outbox_it:
                            if not entry.is_file() or not entry.name.endswith(".json"):
                                continue

                            tick_val = _tick_from_filename_str(entry.name)
                            if tick_val == -1:
                                continue

                            if current_tick - tick_val > max_age_ticks:
                                try:
                                    # Optimization: Use os.unlink directly on entry.path
                                    # to avoid Path object creation and syscall overhead
                                    os.unlink(entry.path)
                                    removed += 1
                                except Exception as exc:  # pragma: no cover
                                    logger.error(
                                        "outbox_cleanup_failed",
                                        extra={
                                            "event": "outbox_cleanup_failed",
                                            "path": entry.path,
                                            "error": str(exc),
                                        },
                                    )
                except OSError:
                    pass
    except OSError:
        pass

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
