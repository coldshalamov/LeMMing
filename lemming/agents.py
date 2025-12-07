from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AgentSchedule:
    run_every_n_ticks: int = 1
    phase_offset: int = 0


@dataclass
class AgentModel:
    key: str
    temperature: float = 0.2
    max_tokens: int = 2048


@dataclass
class AgentPermissions:
    read_outboxes: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)


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

    @classmethod
    def from_resume(cls, resume_path: Path) -> Agent:
        with resume_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        schedule_data = data.get("schedule", {})
        model_data = data.get("model", {})
        permissions_data = data.get("permissions", {})

        return cls(
            name=data["name"],
            path=resume_path.parent,
            title=data["title"],
            short_description=data["short_description"],
            workflow_description=data.get("workflow_description", ""),
            model=AgentModel(
                key=model_data.get("key", "gpt-4.1-mini"),
                temperature=model_data.get("temperature", 0.2),
                max_tokens=model_data.get("max_tokens", 2048),
            ),
            permissions=AgentPermissions(
                read_outboxes=list(permissions_data.get("read_outboxes", [])),
                tools=list(permissions_data.get("tools", [])),
            ),
            schedule=AgentSchedule(
                run_every_n_ticks=schedule_data.get("run_every_n_ticks", 1),
                phase_offset=schedule_data.get("phase_offset", 0),
            ),
            instructions=data["instructions"],
        )


def load_agent(base_path: Path, name: str) -> Agent:
    agent_path = base_path / "agents" / name
    resume_path = agent_path / "resume.json"

    if not resume_path.exists():
        old_resume = agent_path / "resume.txt"
        if old_resume.exists():
            raise FileNotFoundError(f"Agent {name} has old resume.txt. Run scripts/migrate_resumes.py to upgrade.")
        raise FileNotFoundError(f"Missing resume for agent {name} at {resume_path}")

    return Agent.from_resume(resume_path)


def discover_agents(base_path: Path) -> list[Agent]:
    agents_dir = base_path / "agents"
    agents: list[Agent] = []

    if not agents_dir.exists():
        return agents

    for child in agents_dir.iterdir():
        if not child.is_dir() or child.name == "agent_template":
            continue
        resume_path = child / "resume.json"
        if not resume_path.exists():
            logger.warning("Skipping %s; missing resume.json", child.name)
            continue
        try:
            agents.append(Agent.from_resume(resume_path))
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to load agent %s: %s", child.name, exc)

    return agents


def validate_resume(resume_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        with resume_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON: {exc}"]

    required_fields = ["name", "title", "short_description", "model", "permissions", "instructions"]
    for required_field in required_fields:
        if required_field not in data:
            errors.append(f"Missing required field: {required_field}")

    if data.get("name") and data["name"] != resume_path.parent.name:
        errors.append(f"Agent name '{data.get('name')}' does not match directory '{resume_path.parent.name}'")

    model = data.get("model", {})
    if model and "key" not in model:
        errors.append("Missing model.key")

    permissions = data.get("permissions", {})
    if permissions:
        if "read_outboxes" not in permissions:
            errors.append("Missing permissions.read_outboxes")
        if "tools" not in permissions:
            errors.append("Missing permissions.tools")

    return errors
