from __future__ import annotations

import json
from pathlib import Path

from lemming.cli import inbox_cmd, send_cmd, status_cmd
from lemming.messages import OutboxEntry, write_outbox_entry


def _write_config(base_path: Path) -> None:
    config_dir = base_path / "lemming" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "credits.json").write_text("{}", encoding="utf-8")
    (config_dir / "org_config.json").write_text("{}", encoding="utf-8")


def _write_resume(base_path: Path, name: str) -> None:
    resume = {
        "name": name,
        "title": name.title(),
        "short_description": f"Agent {name}",
        "workflow_description": "",
        "model": {"key": "gpt-4.1-mini"},
        "permissions": {"read_outboxes": ["*"], "tools": []},
        "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},
        "instructions": "",
        "credits": {"max_credits": 10, "soft_cap": 5},
    }
    agent_dir = base_path / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "resume.json").write_text(json.dumps(resume), encoding="utf-8")


def test_send_and_inbox_flow(tmp_path: Path, capsys) -> None:
    _write_config(tmp_path)
    _write_resume(tmp_path, "human")
    _write_resume(tmp_path, "alpha")

    send_cmd(tmp_path, "alpha", "hello there")

    human_entries = list((tmp_path / "agents" / "human" / "outbox").glob("*.json"))
    assert human_entries, "send_cmd should write to human outbox"

    response = OutboxEntry.create(
        agent="alpha", tick=1, kind="message", payload={"text": "hi human"}, tags=[]
    )
    write_outbox_entry(tmp_path, "alpha", response)

    inbox_cmd(tmp_path)
    output = capsys.readouterr().out
    assert "alpha" in output
    assert "hi human" in output


def test_status_uses_config(tmp_path: Path, capsys) -> None:
    _write_config(tmp_path)
    _write_resume(tmp_path, "human")

    status_cmd(tmp_path)
    output = capsys.readouterr().out
    assert "LeMMing status" in output
    assert "Agents discovered: 1" in output
    assert "human" in output
