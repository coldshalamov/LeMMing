from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .paths import get_agents_dir, get_resume_json_path, get_resume_txt_path

logger = logging.getLogger(__name__)

DEFAULT_MODEL_KEY = "gpt-4.1-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 2048
DEFAULT_CREDITS = {"max_credits": 1000.0, "soft_cap": 500.0}


@dataclass
class AgentSchedule:
    run_every_n_ticks: int = 1
    phase_offset: int = 0


@dataclass
class AgentModel:
    key: str = DEFAULT_MODEL_KEY
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS


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
    instructions: str
    credits: AgentCredits
    resume_path: Path

    @classmethod
    def from_resume_data(cls, resume_path: Path, data: dict[str, Any]) -> "Agent":
        normalized = _apply_defaults(data)
        errors = _validate_resume_dict(resume_path, normalized)
        if errors:
            raise ValueError("; ".join(errors))

        schedule_data = normalized.get("schedule", {})
        model_data = normalized.get("model", DEFAULT_MODEL_KEY)
        permissions_data = normalized.get("permissions", {})
        credits_data = normalized.get("credits", DEFAULT_CREDITS)

        model = _parse_model(model_data)
        permissions = AgentPermissions(
            read_outboxes=list(permissions_data.get("read_outboxes", [])),
            tools=list(permissions_data.get("tools", [])),
        )
        schedule = AgentSchedule(
            run_every_n_ticks=int(schedule_data.get("run_every_n_ticks", 1)),
            phase_offset=int(schedule_data.get("phase_offset", 0)),
        )
        credits = AgentCredits(
            max_credits=float(credits_data.get("max_credits", DEFAULT_CREDITS["max_credits"])),
            soft_cap=float(credits_data.get("soft_cap", DEFAULT_CREDITS["soft_cap"])),
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
    if isinstance(model_data, str):
        return AgentModel(key=model_data)
    if isinstance(model_data, dict):
        return AgentModel(
            key=model_data.get("key", model_data.get("model", DEFAULT_MODEL_KEY)),
            temperature=float(model_data.get("temperature", DEFAULT_TEMPERATURE)),
            max_tokens=int(model_data.get("max_tokens", DEFAULT_MAX_TOKENS)),
        )
    logger.warning("Unexpected model config format %s; using default", type(model_data))
    return AgentModel()


def _load_resume_json(resume_path: Path) -> dict[str, Any]:
    with resume_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _apply_defaults(data: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(data)
    normalized.setdefault("workflow_description", "")
    normalized.setdefault("short_description", "")
    normalized.setdefault("title", "")
    normalized.setdefault("permissions", {"read_outboxes": [], "tools": []})
    normalized.setdefault("schedule", {"run_every_n_ticks": 1, "phase_offset": 0})
    normalized.setdefault("credits", DEFAULT_CREDITS.copy())
    normalized.setdefault("instructions", "")
    normalized.setdefault("model", DEFAULT_MODEL_KEY)
    return normalized


def _load_resume_txt(resume_path: Path) -> dict[str, Any]:
    text = resume_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines()]

    def _get_value(prefix: str) -> str:
        for line in lines:
            if line.startswith(prefix):
                return line[len(prefix) :].strip()
        return ""

    name = _get_value("Name:") or resume_path.parent.name
    title = _get_value("Role:") or ""
    short_description = _get_value("Description:") or ""

    instructions_block = ""
    if "[INSTRUCTIONS]" in lines:
        start = lines.index("[INSTRUCTIONS]") + 1
        config_idx = lines.index("[CONFIG]") if "[CONFIG]" in lines else len(lines)
        instructions_block = "\n".join(lines[start:config_idx]).strip()

    config_data: dict[str, Any] = {}
    if "[CONFIG]" in lines:
        start = lines.index("[CONFIG]") + 1
        config_lines = "\n".join(lines[start:]).strip()
        try:
            config_data = json.loads(config_lines)
        except json.JSONDecodeError:
            logger.warning("Could not parse CONFIG block in %s", resume_path)

    model = config_data.get("model", DEFAULT_MODEL_KEY)
    if isinstance(model, str):
        model = {"key": model}

    permissions = {
        "read_outboxes": config_data.get("read_from", []),
        "tools": config_data.get("tools", []),
    }

    credits = {
        "max_credits": config_data.get("max_credits", DEFAULT_CREDITS["max_credits"]),
        "soft_cap": config_data.get("soft_cap", DEFAULT_CREDITS["soft_cap"]),
    }

    return {
        "name": name,
        "title": title,
        "short_description": short_description,
        "workflow_description": "",
        "model": model,
        "permissions": permissions,
        "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},
        "instructions": instructions_block,
        "credits": credits,
    }


def _load_resume(base_path: Path, name: str) -> tuple[dict[str, Any], Path] | tuple[None, None]:
    json_path = get_resume_json_path(base_path, name)
    txt_path = get_resume_txt_path(base_path, name)

    if json_path.exists():
        return _load_resume_json(json_path), json_path
    if txt_path.exists():
        return _load_resume_txt(txt_path), txt_path
    return None, None


def _validate_resume_dict(resume_path: Path, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_fields = [
        "name",
        "title",
        "short_description",
        "workflow_description",
        "model",
        "permissions",
        "instructions",
        "schedule",
        "credits",
    ]
    for field_name in required_fields:
        if field_name not in data:
            errors.append(f"Missing required field: {field_name}")

    if data.get("name") and data["name"] != resume_path.parent.name:
        errors.append(
            f"Agent name '{data.get('name')}' does not match directory '{resume_path.parent.name}'"
        )

    permissions = data.get("permissions", {})
    if permissions:
        if "read_outboxes" not in permissions:
            errors.append("Missing permissions.read_outboxes")
        if "tools" not in permissions:
            errors.append("Missing permissions.tools")

    schedule = data.get("schedule", {})
    if schedule:
        n = schedule.get("run_every_n_ticks")
        if n is None or int(n) <= 0:
            errors.append("schedule.run_every_n_ticks must be > 0")
        if "phase_offset" not in schedule:
            errors.append("Missing schedule.phase_offset")

    credits = data.get("credits", {})
    if credits:
        if "max_credits" not in credits:
            errors.append("Missing credits.max_credits")
        if "soft_cap" not in credits:
            errors.append("Missing credits.soft_cap")

    return errors


def load_agent(base_path: Path, name: str) -> Agent:
    data, resume_path = _load_resume(base_path, name)
    if not data or not resume_path:
        raise FileNotFoundError(f"Missing resume for agent {name}")
    return Agent.from_resume_data(resume_path, data)


def discover_agents(base_path: Path) -> list[Agent]:
    agents_dir = get_agents_dir(base_path)
    agents: list[Agent] = []

    if not agents_dir.exists():
        return agents

    for child in agents_dir.iterdir():
        if not child.is_dir() or child.name == "agent_template":
            continue
        try:
            data, resume_path = _load_resume(base_path, child.name)
        except json.JSONDecodeError as exc:
            logger.warning("Skipping %s due to invalid resume JSON: %s", child.name, exc)
            continue
        if not data or not resume_path:
            logger.warning("Skipping %s; missing resume.json or resume.txt", child.name)
            continue
        try:
            agents.append(Agent.from_resume_data(resume_path, data))
        except Exception as exc:  # pragma: no cover
            logger.warning("Skipping %s due to invalid resume: %s", child.name, exc)

    return agents


def validate_resume(resume_path: Path) -> list[str]:
    try:
        if resume_path.suffix == ".json":
            data = _load_resume_json(resume_path)
        else:
            data = _load_resume_txt(resume_path)
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON: {exc}"]
    except Exception as exc:  # pragma: no cover - defensive
        return [str(exc)]

    return _validate_resume_dict(resume_path, data)
