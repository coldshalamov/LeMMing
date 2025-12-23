from __future__ import annotations

import json
from pathlib import Path

import pytest

from lemming.agents import Agent, AgentCredits, AgentModel, AgentPermissions, AgentSchedule
from lemming.engine import run_agent
from lemming.memory import save_memory
from lemming.messages import read_outbox_entries


def _write_credits(base_path: Path, agent_name: str, credits_left: float = 1.0) -> None:
    config_dir = base_path / "lemming" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    credits_path = config_dir / "credits.json"
    credits = {
        agent_name: {
            "model": "gpt-4.1-mini",
            "cost_per_action": 0.01,
            "credits_left": credits_left,
            "max_credits": 10.0,
            "soft_cap": 5.0,
        }
    }
    credits_path.write_text(json.dumps(credits))


def _make_agent(tmp_path: Path, name: str, send_outboxes: list[str] | None = None) -> Agent:
    agent_dir = tmp_path / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    resume_path = agent_dir / "resume.json"
    resume_path.write_text("{}")

    permissions = AgentPermissions(read_outboxes=[], send_outboxes=send_outboxes, tools=[], file_access=None)
    return Agent(
        name=name,
        path=agent_dir,
        title="Test",
        short_description="",
        workflow_description="",
        model=AgentModel(),
        permissions=permissions,
        schedule=AgentSchedule(),
        instructions="",
        credits=AgentCredits(),
        resume_path=resume_path,
    )


def test_memory_delete_operation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = _make_agent(tmp_path, "remover")
    _write_credits(tmp_path, agent.name)
    save_memory(tmp_path, agent.name, "old", {"value": 1})

    monkeypatch.setattr(
        "lemming.engine.call_llm",
        lambda *_, **__: json.dumps(
            {
                "outbox_entries": [],
                "tool_calls": [],
                "memory_updates": [{"key": "old", "op": "delete"}],
                "notes": "",
            }
        ),
    )

    run_agent(tmp_path, agent, tick=1)

    assert not (tmp_path / "agents" / agent.name / "memory" / "old.json").exists()


def test_send_outboxes_enforced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    agent = _make_agent(tmp_path, "sender", send_outboxes=["friend"])
    _write_credits(tmp_path, agent.name)

    monkeypatch.setattr(
        "lemming.engine.call_llm",
        lambda *_, **__: json.dumps(
            {
                "outbox_entries": [
                    {"kind": "message", "payload": {"text": "hi"}, "to": "friend"},
                    {"kind": "message", "payload": {"text": "blocked"}, "to": "stranger"},
                ],
                "tool_calls": [],
                "memory_updates": [],
                "notes": "",
            }
        ),
    )

    caplog.set_level("WARNING")
    run_agent(tmp_path, agent, tick=1)

    entries = read_outbox_entries(tmp_path, agent.name)
    assert len(entries) == 1
    assert entries[0].payload["text"] == "hi"
    assert entries[0].recipients == ["friend"]
    assert any("disallowed recipients" in message for message in caplog.messages)
