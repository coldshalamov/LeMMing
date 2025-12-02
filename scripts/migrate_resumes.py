#!/usr/bin/env python3
"""Migrate resume.txt files to resume.json format."""

from __future__ import annotations

import json
from pathlib import Path


def parse_old_resume(resume_path: Path) -> dict:
    """Parse old resume.txt format into header/instructions/config."""
    content = resume_path.read_text(encoding="utf-8")
    if "[INSTRUCTIONS]" not in content or "[CONFIG]" not in content:
        raise ValueError(f"Resume {resume_path} missing required sections")

    header_text, remainder = content.split("[INSTRUCTIONS]", 1)
    instructions_part, config_part = remainder.split("[CONFIG]", 1)

    header = {}
    for line in header_text.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            header[key.strip().lower()] = value.strip()

    config_json = json.loads(config_part.strip())

    return {
        "header": header,
        "instructions": instructions_part.strip(),
        "config": config_json,
    }


def convert_to_new_format(parsed: dict, agent_name: str) -> dict:
    """Convert parsed resume sections to new JSON format."""
    old_cfg = parsed["config"]
    header = parsed["header"]

    read_outboxes = old_cfg.get("read_from") or ["*"]
    tools = old_cfg.get("tools") or ["memory_read", "memory_write"]
    schedule_multiplier = int(old_cfg.get("org_speed_multiplier", 1))

    return {
        "name": agent_name,
        "title": header.get("role", agent_name.replace("_", " ").title()),
        "short_description": header.get("description", "A LeMMing agent."),
        "workflow_description": "",
        "model": {
            "key": old_cfg.get("model", "gpt-4.1-mini"),
            "temperature": 0.2,
            "max_tokens": 2048,
        },
        "permissions": {
            "read_outboxes": read_outboxes,
            "tools": tools,
        },
        "schedule": {
            "run_every_n_ticks": schedule_multiplier,
            "phase_offset": 0,
        },
        "instructions": parsed["instructions"],
    }


def migrate_agent(agent_dir: Path) -> None:
    old_resume = agent_dir / "resume.txt"
    new_resume = agent_dir / "resume.json"

    if not old_resume.exists():
        print(f"Skipping {agent_dir.name}: no resume.txt")
        return
    if new_resume.exists():
        print(f"Skipping {agent_dir.name}: resume.json already exists")
        return

    parsed = parse_old_resume(old_resume)
    new_format = convert_to_new_format(parsed, agent_dir.name)

    with new_resume.open("w", encoding="utf-8") as f:
        json.dump(new_format, f, indent=2)

    print(f"Migrated {agent_dir.name}")


def main() -> None:
    base_path = Path(__file__).resolve().parent.parent
    agents_dir = base_path / "agents"
    for agent_dir in agents_dir.iterdir():
        if agent_dir.is_dir():
            migrate_agent(agent_dir)


if __name__ == "__main__":
    main()
