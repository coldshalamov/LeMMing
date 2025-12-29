from __future__ import annotations

import json
from pathlib import Path

import pytest

from lemming import cli


def _setup_cli_base(tmp_path: Path) -> Path:
    config_dir = tmp_path / "lemming" / "config"
    config_dir.mkdir(parents=True)

    (config_dir / "org_config.json").write_text(
        json.dumps({"base_turn_seconds": 1, "max_turns": None}), encoding="utf-8"
    )
    (config_dir / "credits.json").write_text(
        json.dumps({"demo": {"model": "demo", "credits_left": 3.0}}), encoding="utf-8"
    )

    agent_dir = tmp_path / "agents" / "demo"
    agent_dir.mkdir(parents=True)
    resume = {
        "name": "demo",
        "title": "Demo Agent",
        "short_description": "A demo agent description",
        "workflow_description": "",
        "model": {"key": "demo"},
        "permissions": {"read_outboxes": [], "tools": []},
        "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},
        "instructions": "",
    }
    (agent_dir / "resume.json").write_text(json.dumps(resume), encoding="utf-8")

    return tmp_path


def test_list_agents_cmd_outputs_table(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    base = _setup_cli_base(tmp_path)

    cli.list_agents_cmd(base)
    output = capsys.readouterr().out

    assert "Demo Agent" in output
    assert "demo" in output


def test_status_cmd_reports_counts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    base = _setup_cli_base(tmp_path)

    cli.status_cmd(base)
    output = capsys.readouterr().out

    assert "Current tick" in output
    assert "Agents discovered: 1" in output
    assert "Total credits remaining: 3.0" in output
