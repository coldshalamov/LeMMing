from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_outbox_path(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    processed = path / "processed"
    processed.mkdir(parents=True, exist_ok=True)


def cleanup_expired_messages(base_path: Path, current_turn: int) -> None:
    agents_dir = base_path / "agents"
    for agent_dir in agents_dir.iterdir():
        outbox_dir = agent_dir / "outbox"
        if not outbox_dir.exists():
            continue
        for receiver_dir in outbox_dir.iterdir():
            if not receiver_dir.is_dir():
                continue
            for msg_file in receiver_dir.glob("msg_*.json"):
                try:
                    with msg_file.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    ttl_turns = data.get("ttl_turns")
                    turn_created = data.get("turn_created", 0)
                    if ttl_turns is not None and turn_created + ttl_turns < current_turn:
                        msg_file.unlink(missing_ok=True)
                        logger.info("Cleaned expired message %s", msg_file)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.error("Failed to clean message %s: %s", msg_file, exc)
