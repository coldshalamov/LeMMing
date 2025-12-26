from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .paths import get_agents_dir, get_resume_json_path

logger = logging.getLogger(__name__)

# Cache for Agent objects: path -> (mtime, Agent)
_agent_cache: dict[Path, tuple[float, Agent]] = {}


def reset_agents_cache() -> None:
    global _agent_cache
    _agent_cache.clear()


DEFAULT_MODEL_KEY = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 2048
DEFAULT_CREDITS = {"max_credits": 1000.0, "soft_cap": 500.0}


def _default_credits() -> AgentCredits:
    return AgentCredits(max_credits=DEFAULT_CREDITS["max_credits"], soft_cap=DEFAULT_CREDITS["soft_cap"])


@dataclass
class AgentSchedule:
    run_every_n_ticks: int = 1
    phase_offset: int = 0


@dataclass
class AgentModel:
    key: str = DEFAULT_MODEL_KEY
    temperature: float | None = DEFAULT_TEMPERATURE
    max_tokens: int | None = DEFAULT_MAX_TOKENS


@dataclass
class AgentPermissions:
    read_outboxes: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)


@dataclass
class AgentCredits:
    max_credits: float = DEFAULT_CREDITS["max_credits"]
    soft_cap: float = DEFAULT_CREDITS["soft_cap"]


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
    resume_path: Path
    instructions: str = ""
    credits: AgentCredits = field(default_factory=_default_credits)

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

        model = _parse_model(model_data) if model_data is not None else AgentModel()

        permissions = AgentPermissions(
            read_outboxes=list(permissions_data["read_outboxes"]),
            tools=list(permissions_data["tools"]),
        )
        schedule = AgentSchedule(
            run_every_n_ticks=int(schedule_data["run_every_n_ticks"]),
            phase_offset=int(schedule_data["phase_offset"]),
        )
        credits = (
            AgentCredits(
                max_credits=float(credits_data["max_credits"]),
                soft_cap=float(credits_data["soft_cap"]),
            )
            if credits_data is not None
            else _default_credits()
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

    if "instructions" not in data or not isinstance(data.get("instructions"), str):
        errors.append("instructions must be a string")

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

    # Walk recursively to support sub-orgs (e.g., agents/sales/lead/resume.json)
    for root, dirs, files in os.walk(agents_dir):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        # Skip the agent_template directory at top level
        # Note: We check if the *current* root is the template dir, or if we are about to enter it
        rel_path = Path(root).relative_to(agents_dir)
        if str(rel_path).startswith("agent_template") or "agent_template" in dirs:
            if "agent_template" in dirs:
                dirs.remove("agent_template")
            if str(rel_path).startswith("agent_template"):
                continue

        if "resume.json" in files:
            resume_path = Path(root) / "resume.json"
            folder_name = resume_path.parent.name

            # Optimization: check cache based on mtime
            try:
                stat_result = resume_path.stat()
                mtime = stat_result.st_mtime

                # If cached and mtime matches, use cached agent
                if resume_path in _agent_cache:
                    cached_mtime, cached_agent = _agent_cache[resume_path]
                    if cached_mtime == mtime:
                        if cached_agent.name in seen_names:
                            logger.warning(
                                "duplicate_agent_name",
                                extra={
                                    "event": "duplicate_agent_name",
                                    "path": str(resume_path.parent),
                                    "agent": cached_agent.name,
                                },
                            )
                            continue

                        seen_names.add(cached_agent.name)
                        agents.append(cached_agent)
                        continue
            except FileNotFoundError:
                logger.warning(
                    "resume_missing",
                    extra={"event": "resume_missing", "path": str(resume_path.parent)},
                )
                continue

            # Fallback: load from disk
            try:
                data = _load_resume_json(resume_path)
            except json.JSONDecodeError as exc:
                logger.warning(
                    "resume_invalid_json",
                    extra={
                        "event": "resume_invalid_json",
                        "path": str(resume_path.parent),
                        "error": str(exc),
                    },
                )
                continue

            resume_name = data.get("name")
            if resume_name and resume_name != folder_name:
                # In nested structures, folder name strict match is less critical,
                # but nice for sanity. We'll warn but allow it if it differs,
                # unless you want strict enforcement.
                # Project rules say: simplicity. Let's warn.
                logger.warning(
                    "resume_name_mismatch",
                    extra={
                        "event": "resume_name_mismatch",
                        "folder": folder_name,
                        "resume": resume_name,
                        "path": str(resume_path),
                    },
                )

            try:
                agent = Agent.from_resume_data(resume_path, data)
                # Update cache
                _agent_cache[resume_path] = (mtime, agent)
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "resume_invalid",
                    extra={
                        "event": "resume_invalid",
                        "path": str(resume_path.parent),
                        "error": str(exc),
                    },
                )
                continue

            if agent.name in seen_names:
                logger.warning(
                    "duplicate_agent_name",
                    extra={
                        "event": "duplicate_agent_name",
                        "path": str(resume_path.parent),
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


def validate_resume_data(data: dict[str, Any], resume_path: Path | None = None) -> list[str]:
    """Validate in-memory resume data using the same rules as resume.json files."""
    path = resume_path or Path("<resume.json>")
    normalized = dict(data)
    return _validate_resume_dict(path, normalized)
