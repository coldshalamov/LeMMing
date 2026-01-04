from __future__ import annotations

import heapq
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
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
    """Scans outbox files and returns list of (tick, full_path_str) without loading content.

    This is faster than read_outbox_entries when we only need to sort by tick/filename
    across multiple agents.

    If limit > 0, returns only the most recent 'limit' entries using heapq.
    """
    return [
        (tick, path)
        for tick, path, _ in _scan_outbox_files_optimized(base_path, agent_name, since_tick, limit)
    ]


def _scan_outbox_files_optimized(
    base_path: Path, agent_name: str, since_tick: int | None = None, limit: int = 0
) -> list[tuple[int, str, str]]:
    """Internal optimized version returning (tick, full_path_str, filename)."""
    outbox_dir = get_outbox_dir(base_path, agent_name)
    if not outbox_dir.exists():
        return []

    results = []
    try:
        with os.scandir(outbox_dir) as it:
            if limit > 0:
                # Use a generator to avoid creating the full list of files
                # Optimization: Filter by .json and ensure start with digit (valid tick)
                # This avoids processing garbage files like 'temp.json' which would sort
                # incorrectly in string comparison.
                candidate_files = (
                    entry
                    for entry in it
                    if entry.is_file()
                    and entry.name.endswith(".json")
                    and entry.name[0].isdigit()
                )

                # nlargest returns the largest elements, so highest tick (newest).
                # We need to include the full path in the result
                # Optimization: Use string comparison (via entry.name) instead of int parsing.
                # Since ticks are zero-padded (08d) and filenames start with tick,
                # string sort is equivalent to tick sort for valid files.
                largest_entries = heapq.nlargest(
                    limit,
                    candidate_files,
                    key=lambda e: e.name,
                )

                for entry in largest_entries:
                    tick = _tick_from_filename_str(entry.name)
                    # No need to check tick != -1 strictly if we trust nlargest handles it,
                    # but _tick_from_filename_str returns -1 on error.
                    if tick != -1:
                        if since_tick is not None and tick < since_tick:
                            continue
                        results.append((tick, entry.path, entry.name))

            else:
                for entry in it:
                    if entry.is_file() and entry.name.endswith(".json"):
                        tick = _tick_from_filename_str(entry.name)
                        if tick != -1:
                            if since_tick is not None and tick < since_tick:
                                continue
                            results.append((tick, entry.path, entry.name))
    except FileNotFoundError:
        pass
    return results


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
    # Optimization: Use os.scandir to avoid creating Path objects for all files.
    # Use heapq.nlargest to avoid sorting all files when we only need the top K.
    try:
        with os.scandir(outbox_dir) as it:
            # Helper generator to filter non-json files
            candidate_files = (
                entry.name for entry in it if entry.is_file() and entry.name.endswith(".json")
            )

            # If since_tick is provided, we can pre-filter files that are definitely too old
            # IF the filename tick parsing is reliable. It is.
            if since_tick is not None:
                candidate_files = (
                    name for name in candidate_files if _tick_from_filename_str(name) >= since_tick
                )

            filenames = heapq.nlargest(limit, candidate_files, key=None)
    except FileNotFoundError:
        return []

    min_collected_tick = float("inf")

    for name in filenames:
        entry_path = outbox_dir / name
        tick_val = _tick_from_filename(entry_path)

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
    if read_outboxes == ["*"]:
        agents_dir = get_agents_dir(base_path)
        if not agents_dir.exists():
            return []
        read_outboxes = [
            d.name for d in agents_dir.iterdir() if d.is_dir() and d.name not in {agent_name, "agent_template"}
        ]
        # Optimization: Use os.scandir to avoid creating Path objects
        with os.scandir(agents_dir) as it:
            read_outboxes = [
                entry.name
                for entry in it
                if entry.is_dir() and entry.name not in {agent_name, "agent_template"}
            ]

    # Optimization: Scan metadata first to avoid loading content of old messages
    # Optimization: Use heapq.merge to combine sorted results from multiple agents efficiently
    # instead of extend + sort. scan_outbox_files returns results sorted by (tick, filename) desc
    # when limit > 0 (via nlargest). If limit=0, it's unsorted, so we must sort if limit=0,
    # but collect_readable_outboxes typically uses a limit.
    # To be safe and consistent, we'll collect all iterables and merge them.
    # scan_outbox_files returns (tick, path, filename).

    iterables = []
    for other in read_outboxes:
        if other == agent_name:
            continue
        # Pass the limit to scan_outbox_files to reduce memory usage and processing
        # Each agent returns at most 'limit' newest messages.
        res = _scan_outbox_files_optimized(base_path, other, since_tick=since_tick, limit=limit)
        # Ensure the result is sorted because scan_outbox_files(limit > 0) returns sorted by name desc.
        # Name sort is equivalent to (tick, filename) desc.
        # If limit=0, scan_outbox_files is NOT sorted.
        if limit == 0:
            res.sort(key=lambda x: x[2], reverse=True)  # Sort by filename (includes tick)
        iterables.append(res)

    # Use heapq.merge to merge the sorted lists
    merged_iter = heapq.merge(*iterables, key=lambda x: x[2], reverse=True)

    entries: list[OutboxEntry] = []
    candidates: list[tuple[int, str]] = []

    # Optimization: consume the merged iterator directly
    # We must collect enough candidates to cover 'limit' PLUS any ties at the boundary.
    # The merged_iter is sorted by filename descending (newest first).
    # We can stop once we have > limit items AND the current item's tick is strictly less than the limit-th item's tick.
    # Actually, we can just collect 'limit' items, check the tick of the last one, and then continue collecting
    # items with the SAME tick.

    count = 0
    cutoff_tick = -1

    for tick, path_str, _ in merged_iter:
        if count >= limit:
            if cutoff_tick == -1:
                cutoff_tick = candidates[limit - 1][0]

            # If we've reached the limit, only continue if the current item has the same tick as the cutoff
            if tick < cutoff_tick:
                break

        candidates.append((tick, path_str))
        count += 1

    for _, path_str in candidates:
        entry = _load_entry(Path(path_str))
        if entry is None:
            continue
        entries.append(entry)

    entries.sort(key=lambda e: (e.tick, e.created_at), reverse=True)
    return entries[:limit]


def cleanup_old_outbox_entries(base_path: Path, current_tick: int, max_age_ticks: int = 100) -> int:
    removed = 0
    agents_dir = get_agents_dir(base_path)
    if not agents_dir.exists():
        return 0

    # Optimization: Use os.scandir to iterate agents efficiently
    try:
        with os.scandir(agents_dir) as it:
            for agent_entry in it:
                if not agent_entry.is_dir():
                    continue

                outbox_dir = get_outbox_dir(base_path, agent_entry.name)
                if not outbox_dir.exists():
                    continue

                try:
                    with os.scandir(outbox_dir) as outbox_it:
                        for entry in outbox_it:
                            if not entry.is_file() or not entry.name.endswith(".json"):
                                continue

                            tick_val = _tick_from_filename_str(entry.name)
                            if tick_val == -1:
                                continue

                            if current_tick - tick_val > max_age_ticks:
                                entry_path = outbox_dir / entry.name
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
