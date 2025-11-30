from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class Agent:
    name: str
    path: Path
    model_key: str
    org_speed_multiplier: int
    send_to: List[str]
    read_from: List[str]
    max_credits: float
    resume_text: str
    instructions_text: str
    config_json: Dict[str, Any]
    role: str
    description: str


def parse_resume(resume_path: Path) -> Dict[str, Any]:
    with resume_path.open("r", encoding="utf-8") as f:
        content = f.read()
    sections = content.split("[INSTRUCTIONS]")
    header = sections[0].strip().splitlines()
    instructions_and_config = sections[1] if len(sections) > 1 else ""
    instructions_part, config_part = instructions_and_config.split("[CONFIG]")
    instructions_text = instructions_part.strip()
    config_json = json.loads(config_part.strip())

    header_map: Dict[str, str] = {}
    for line in header:
        if ":" in line:
            key, value = line.split(":", 1)
            header_map[key.strip().lower()] = value.strip()

    return {
        "name": header_map.get("name", ""),
        "role": header_map.get("role", ""),
        "description": header_map.get("description", ""),
        "instructions_text": instructions_text,
        "config_json": config_json,
        "resume_text": content,
    }


def load_agent(base_path: Path, name: str) -> Agent:
    agent_path = base_path / "agents" / name
    resume_path = agent_path / "resume.txt"
    if not resume_path.exists():
        raise FileNotFoundError(f"Missing resume for agent {name} at {resume_path}")
    parsed = parse_resume(resume_path)
    cfg = parsed["config_json"]
    return Agent(
        name=name,
        path=agent_path,
        model_key=cfg.get("model", "gpt-4.1-mini"),
        org_speed_multiplier=int(cfg.get("org_speed_multiplier", 1)),
        send_to=list(cfg.get("send_to", [])),
        read_from=list(cfg.get("read_from", [])),
        max_credits=float(cfg.get("max_credits", 0.0)),
        resume_text=parsed["resume_text"],
        instructions_text=parsed["instructions_text"],
        config_json=cfg,
        role=parsed.get("role", ""),
        description=parsed.get("description", ""),
    )


def discover_agents(base_path: Path) -> List[Agent]:
    agents_dir = base_path / "agents"
    agents: List[Agent] = []
    if not agents_dir.exists():
        return agents
    for child in agents_dir.iterdir():
        if not child.is_dir():
            continue
        if child.name == "agent_template":
            continue
        resume_path = child / "resume.txt"
        if resume_path.exists():
            try:
                agents.append(load_agent(base_path, child.name))
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to load agent %s: %s", child.name, exc)
    return agents


def bootstrap_agent_from_template(base_path: Path, name: str, role_config: Dict[str, Any]) -> Agent:
    template_dir = base_path / "agents" / "agent_template"
    target_dir = base_path / "agents" / name
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy template structure
    for sub in ["outbox", "memory", "logs", "config"]:
        (target_dir / sub).mkdir(parents=True, exist_ok=True)

    template_resume = template_dir / "resume.txt"
    if not template_resume.exists():
        raise FileNotFoundError("Template resume not found; run bootstrap to create it")
    with template_resume.open("r", encoding="utf-8") as f:
        template_text = f.read()

    # Replace fields
    resume_lines = []
    for line in template_text.splitlines():
        if line.startswith("Name: "):
            resume_lines.append(f"Name: {role_config.get('name', name)}")
        elif line.startswith("Role: "):
            resume_lines.append(f"Role: {role_config.get('role', 'Generic agent')}")
        elif line.startswith("Description: "):
            resume_lines.append(f"Description: {role_config.get('description', '')}")
        else:
            resume_lines.append(line)
    resume_text = "\n".join(resume_lines)

    # Replace config block
    if "[CONFIG]" in resume_text:
        parts = resume_text.split("[CONFIG]")
        resume_text = f"{parts[0]}[CONFIG]\n{json.dumps(role_config.get('config', {}), indent=2)}\n"
    with (target_dir / "resume.txt").open("w", encoding="utf-8") as f:
        f.write(resume_text)

    return load_agent(base_path, name)
