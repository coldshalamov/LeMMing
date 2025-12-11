from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import get_agents_dir, get_resume_json_path

logger = logging.getLogger(__name__)

DEFAULT_MODEL_KEY = "gpt-4.1-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 2048
DEFAULT_CREDITS = {"max_credits": 1000.0, "soft_cap": 500.0}


@dataclass
class AgentSchedule:
    run_every_n_ticks: int
    phase_offset: int


@dataclass
class AgentModel:
    key: str
    temperature: float | None = None
    max_tokens: int | None = None


@dataclass
class FileAccess:
    """File access permissions for agents."""

    allow_read: list[str]
    allow_write: list[str]


@dataclass
class AgentPermissions:
    read_outboxes: list[str]
    send_outboxes: list[str] | None
    tools: list[str]
    file_access: FileAccess | None


@dataclass
class AgentCredits:
    max_credits: float
    soft_cap: float


@dataclass
class Agent:
    name: str
    path: Path
    title: str
    short_description: str
    workflow_description: str
    model: AgentModel
    permissions: AgentPermissions
    schedule: AgentSchedule
    instructions: str
    credits: AgentCredits | None
    resume_path: Path

    @classmethod
    def from_resume_data(cls, resume_path: Path, data: dict[str, Any]) -> Agent:
        normalized = dict(data)
        errors = _validate_resume_dict(resume_path, normalized)
        if errors:
            raise ValueError("; ".join(errors))

        schedule_data = normalized["schedule"]
        model_data = normalized["model"]
        permissions_data = normalized["permissions"]
        credits_data = normalized.get("credits")

        model = _parse_model(model_data)

        file_access_data = permissions_data.get("file_access")
        file_access = None
        if isinstance(file_access_data, dict):
            file_access = FileAccess(
                allow_read=list(file_access_data.get("allow_read", [])),
                allow_write=list(file_access_data.get("allow_write", [])),
            )

        send_outboxes = permissions_data.get("send_outboxes")
        if send_outboxes is not None:
            send_outboxes = list(send_outboxes)

        permissions = AgentPermissions(
            read_outboxes=list(permissions_data["read_outboxes"]),
            send_outboxes=send_outboxes,
            tools=list(permissions_data["tools"]),
            file_access=file_access,
        )
        schedule = AgentSchedule(
            run_every_n_ticks=int(schedule_data["run_every_n_ticks"]),
            phase_offset=int(schedule_data["phase_offset"]),
        )
        credits = None
        if credits_data is not None:
            credits = AgentCredits(
                max_credits=float(credits_data["max_credits"]),
                soft_cap=float(credits_data["soft_cap"]),
            )

        return cls(
            name=normalized["name"],
            path=resume_path.parent,
            title=normalized["title"],
            short_description=normalized["short_description"],
            workflow_description=normalized.get("workflow_description", ""),
            model=model,
            permissions=permissions,
            schedule=schedule,
            instructions=normalized["instructions"],
            credits=credits,
            resume_path=resume_path,
        )


def _parse_model(model_data: Any) -> AgentModel:
    if isinstance(model_data, dict):
        key_value = model_data.get("key")
        if not isinstance(key_value, str) or not key_value:
            raise ValueError("model.key must be a non-empty string")

        temperature = model_data.get("temperature")
        max_tokens = model_data.get("max_tokens")
        return AgentModel(
            key=key_value,
            temperature=float(temperature) if temperature is not None else None,
            max_tokens=int(max_tokens) if max_tokens is not None else None,
        )
    raise ValueError("model must be an object with a key field")


def _load_resume_json(resume_path: Path) -> dict[str, Any]:
    with resume_path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


def _validate_resume_dict(resume_path: Path, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_fields = ["name", "title", "short_description", "model", "permissions", "schedule", "instructions"]
    for field_name in required_fields:
        if field_name not in data:
            errors.append(f"Missing required field: {field_name}")

    if errors:
        return errors

    permissions = data.get("permissions")
    if not isinstance(permissions, dict):
        errors.append("permissions must be an object")
        return errors

    for key in ["read_outboxes", "tools"]:
        if key not in permissions:
            errors.append(f"Missing permissions.{key}")
        elif not isinstance(permissions.get(key), list):
            errors.append(f"permissions.{key} must be a list")

    for key in ["send_outboxes"]:
        value = permissions.get(key)
        if value is not None and not isinstance(value, list):
            errors.append(f"permissions.{key} must be a list when provided")

    file_access = permissions.get("file_access")
    if file_access is not None:
        if not isinstance(file_access, dict):
            errors.append("permissions.file_access must be a dict when provided")
        else:
            for key in ["allow_read", "allow_write"]:
                if key not in file_access:
                    errors.append(f"Missing permissions.file_access.{key}")
                elif not isinstance(file_access.get(key), list):
                    errors.append(f"permissions.file_access.{key} must be a list")

    schedule = data.get("schedule")
    if not isinstance(schedule, dict):
        errors.append("schedule must be an object")
    else:
        if "run_every_n_ticks" not in schedule:
            errors.append("Missing schedule.run_every_n_ticks")
        elif int(schedule.get("run_every_n_ticks", 0)) <= 0:
            errors.append("schedule.run_every_n_ticks must be > 0")

        if "phase_offset" not in schedule:
            errors.append("Missing schedule.phase_offset")
        elif not isinstance(schedule.get("phase_offset"), int):
            errors.append("schedule.phase_offset must be an integer")

    model = data.get("model")
    if not isinstance(model, dict):
        errors.append("model must be an object")
    else:
        if "key" not in model or not isinstance(model.get("key"), str) or not model.get("key"):
            errors.append("Missing model.key")
        for numeric_field in ["temperature"]:
            if numeric_field in model:
                try:
                    float(model[numeric_field])
                except (TypeError, ValueError):
                    errors.append(f"model.{numeric_field} must be a number")
        if "max_tokens" in model:
            try:
                int(model["max_tokens"])
            except (TypeError, ValueError):
                errors.append("model.max_tokens must be an integer")

    credits = data.get("credits")
    if credits is not None:
        if not isinstance(credits, dict):
            errors.append("credits must be an object when provided")
        else:
            for key in ["max_credits", "soft_cap"]:
                if key not in credits:
                    errors.append(f"Missing credits.{key}")
                else:
                    try:
                        float(credits[key])
                    except (TypeError, ValueError):
                        errors.append(f"credits.{key} must be a number")

    if not isinstance(data.get("instructions"), str) or not data.get("instructions"):
        errors.append("instructions must be a non-empty string")

    if not isinstance(data.get("title"), str) or not data.get("title"):
        errors.append("title must be a non-empty string")

    if not isinstance(data.get("short_description"), str) or not data.get("short_description"):
        errors.append("short_description must be a non-empty string")

    if "name" in data and (not isinstance(data.get("name"), str) or not data.get("name")):
        errors.append("name must be a non-empty string")

    return errors


def load_agent(base_path: Path, name: str) -> Agent:
    resume_path = get_resume_json_path(base_path, name)
    if not resume_path.exists():
        raise FileNotFoundError(f"Missing resume.json for agent {name}")

    data = _load_resume_json(resume_path)
    return Agent.from_resume_data(resume_path, data)


def discover_agents(base_path: Path) -> list[Agent]:
    agents_dir = get_agents_dir(base_path)
    agents: list[Agent] = []
    seen_names: set[str] = set()

    if not agents_dir.exists():
        return agents

    for child in agents_dir.iterdir():
        if not child.is_dir() or child.name == "agent_template":
            continue
        resume_path = get_resume_json_path(base_path, child.name)
        if not resume_path.exists():
            logger.warning(
                "resume_missing",
                extra={"event": "resume_missing", "path": str(child)},
            )
            continue
        try:
            data = _load_resume_json(resume_path)
        except json.JSONDecodeError as exc:
            logger.warning(
                "resume_invalid_json",
                extra={
                    "event": "resume_invalid_json",
                    "path": str(child),
                    "error": str(exc),
                },
            )
            continue

        resume_name = data.get("name")
        if resume_name and resume_name != child.name:
            logger.warning(
                "resume_name_mismatch",
                extra={
                    "event": "resume_name_mismatch",
                    "folder": child.name,
                    "resume": resume_name,
                },
            )

        try:
            agent = Agent.from_resume_data(resume_path, data)
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "resume_invalid",
                extra={
                    "event": "resume_invalid",
                    "path": str(child),
                    "error": str(exc),
                },
            )
            continue

        if agent.name in seen_names:
            logger.warning(
                "duplicate_agent_name",
                extra={
                    "event": "duplicate_agent_name",
                    "folder": child.name,
                    "agent": agent.name,
                },
            )
            continue

        seen_names.add(agent.name)
        agents.append(agent)

    return agents


def validate_resume(resume_path: Path) -> list[str]:
    if resume_path.suffix != ".json":
        return ["resume must be a JSON file"]

    try:
        data = _load_resume_json(resume_path)
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON: {exc}"]
    except Exception as exc:  # pragma: no cover - defensive
        return [str(exc)]

    return _validate_resume_dict(resume_path, data)
