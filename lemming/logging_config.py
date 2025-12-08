"""Structured logging configuration for LeMMing."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        extra_fields = [
            "agent",
            "tick",
            "action",
            "duration_ms",
            "error",
            "fire_point",
            "credits_left",
            "tool_name",
            "outbox_count",
            "memory_updates",
        ]
        for key in extra_fields:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(base_path: Path, level: str = "INFO", console_output: bool = True) -> None:
    """Configure structured logging for LeMMing.

    Args:
        base_path: Base path for the repository
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to also log to console
    """
    # Ensure logs directory exists
    logs_dir = base_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Engine logger - writes to logs/engine.log
    engine_log = logs_dir / "engine.log"
    engine_handler = logging.FileHandler(engine_log)
    engine_handler.setFormatter(StructuredFormatter())

    # Set up root logger for lemming
    root = logging.getLogger("lemming")
    root.setLevel(getattr(logging, level.upper()))
    root.handlers.clear()  # Clear any existing handlers
    root.addHandler(engine_handler)

    # Optionally add console handler for human-readable output
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root.addHandler(console_handler)


def get_agent_logger(base_path: Path, agent_name: str) -> logging.Logger:
    """Get a logger for a specific agent.

    Creates a per-agent log file at agents/<name>/logs/activity.log

    Args:
        base_path: Base path for the repository
        agent_name: Name of the agent

    Returns:
        Logger instance for the agent
    """
    log_path = base_path / "agents" / agent_name / "logs" / "activity.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(f"lemming.agent.{agent_name}")

    # Only add handler if it doesn't already exist
    if not logger.handlers:
        handler = logging.FileHandler(log_path)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        # Don't propagate to root to avoid duplicate logs
        logger.propagate = False

    return logger


def log_agent_action(
    base_path: Path,
    agent_name: str,
    tick: int,
    action: str,
    **extra: Any,
) -> None:
    """Log an agent action with structured data.

    Args:
        base_path: Base path for the repository
        agent_name: Name of the agent
        tick: Current tick number
        action: Action being performed
        **extra: Additional fields to include in the log
    """
    logger = get_agent_logger(base_path, agent_name)
    logger.info(
        action,
        extra={
            "agent": agent_name,
            "tick": tick,
            "action": action,
            **extra,
        },
    )


def log_engine_event(
    message: str,
    level: str = "INFO",
    **extra: Any,
) -> None:
    """Log an engine event with structured data.

    Args:
        message: Log message
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        **extra: Additional fields to include in the log
    """
    logger = logging.getLogger("lemming.engine")
    log_level = getattr(logging, level.upper())
    logger.log(log_level, message, extra=extra)
