from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from . import org
from .file_dispatcher import ensure_outbox_path

logger = logging.getLogger(__name__)


@dataclass
class Message:
    id: str
    sender: str
    receiver: str
    timestamp: str
    importance: str
    ttl_turns: int | None
    content: str
    instructions: str | None
    turn_created: int


def _message_path(base_path: Path, msg: Message) -> Path:
    return base_path / "agents" / msg.sender / "outbox" / msg.receiver / f"msg_{msg.id}.json"


def send_message(base_path: Path, msg: Message) -> None:
    if not org.can_send(msg.sender, msg.receiver, base_path):
        raise PermissionError(f"{msg.sender} cannot send to {msg.receiver} per org chart")
    path = _message_path(base_path, msg)
    ensure_outbox_path(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(msg), f, indent=2)
    logger.info("Message %s sent from %s to %s", msg.id, msg.sender, msg.receiver)


def collect_incoming_messages(base_path: Path, agent_name: str, current_turn: int) -> List[Message]:
    incoming: List[Message] = []
    read_from = org.get_read_from(agent_name, base_path)
    for other in read_from:
        inbox_dir = base_path / "agents" / other / "outbox" / agent_name
        if not inbox_dir.exists():
            continue
        for path in inbox_dir.glob("msg_*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                msg = Message(**data)
                if msg.ttl_turns is not None and msg.turn_created + msg.ttl_turns < current_turn:
                    logger.debug("Skipping expired message %s for %s", msg.id, agent_name)
                    continue
                incoming.append(msg)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to load message %s: %s", path, exc)
    return incoming


def mark_message_processed(base_path: Path, message: Message) -> None:
    path = _message_path(base_path, message)
    if not path.exists():
        return
    processed_dir = path.parent / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    target = processed_dir / path.name
    path.rename(target)
    logger.debug("Marked message %s as processed", message.id)


def create_message(sender: str, receiver: str, content: str, importance: str = "normal", ttl_turns: int | None = 24, instructions: str | None = None, current_turn: int = 0) -> Message:
    return Message(
        id=str(uuid.uuid4()),
        sender=sender,
        receiver=receiver,
        timestamp=datetime.now(timezone.utc).isoformat(),
        importance=importance,
        ttl_turns=ttl_turns,
        content=content,
        instructions=instructions,
        turn_created=current_turn,
    )
