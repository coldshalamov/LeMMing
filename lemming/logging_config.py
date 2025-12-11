"""Structured logging configuration for LeMMing."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_EXTRA_FIELDS: tuple[str, ...] = (
    "agent",
    "tick",
    "event",
    "duration_ms",
    "llm_duration_ms",
    "fire_point",
    "credits_left",
    "tool_name",
    "tool_count",
    "outbox_count",
    "memory_updates",
    "agent_count",
    "reason",
    "error",
    "entries_removed",
    "message_count",
    "model_name",
    "recipients",
    "key",
    "backoff_seconds",
    "max_attempts",
    "failures",
    "state",
    "path",
    "content_length",
    "attempt",
    "snippet",
    "agents",
)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON line."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
        }

        event = getattr(record, "event", None)
        message = record.getMessage()
        if event:
            log_data["event"] = event
        if message and message != event:
            log_data["message"] = message

        for key in DEFAULT_EXTRA_FIELDS:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(
    base_path: Path,
    level: str = "INFO",
    console_output: bool = True,
    module_levels: dict[str, str] | None = None,
) -> None:
    """Configure structured logging for LeMMing.

    Args:
        base_path: Base path for the repository
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to also log to console
        module_levels: Optional per-module level overrides (module -> level name)
    """
    logs_dir = base_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    engine_log = logs_dir / "structured.jsonl"
    engine_handler = logging.FileHandler(engine_log)
    engine_handler.setFormatter(StructuredFormatter())

    root = logging.getLogger("lemming")
    root.setLevel(getattr(logging, level.upper()))
    root.handlers.clear()
    root.addHandler(engine_handler)

    if module_levels:
        for module_name, module_level in module_levels.items():
            logging.getLogger(f"lemming.{module_name}").setLevel(
                getattr(logging, module_level.upper())
            )

    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredFormatter())
        root.addHandler(console_handler)


def get_agent_logger(base_path: Path, agent_name: str) -> logging.Logger:
    """Get a logger for a specific agent.

    Creates a per-agent log file at agents/<name>/logs/structured.jsonl
    """

    log_path = base_path / "agents" / agent_name / "logs" / "structured.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(f"lemming.agent.{agent_name}")

    if not logger.handlers:
        handler = logging.FileHandler(log_path)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger


def log_agent_action(
    base_path: Path,
    agent_name: str,
    tick: int,
    action: str,
    **extra: Any,
) -> None:
    """Log an agent action with structured data."""

    logger = get_agent_logger(base_path, agent_name)
    logger.info(
        action,
        extra={
            "agent": agent_name,
            "tick": tick,
            "event": action,
            **extra,
        },
    )


def log_engine_event(
    message: str,
    level: str = "INFO",
    **extra: Any,
) -> None:
    """Log an engine event with structured data."""

    logger = logging.getLogger("lemming.engine")
    log_level = getattr(logging, level.upper())
    logger.log(log_level, message, extra={"event": message, **extra})
