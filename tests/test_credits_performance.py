from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from lemming import org
from lemming.agents import Agent, AgentCredits, AgentModel, AgentPermissions, AgentSchedule
from lemming.engine import run_tick


def _make_agent(tmp_path: Path, name: str) -> Agent:
    agent_dir = tmp_path / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    resume_path = agent_dir / "resume.json"
    resume_path.write_text("{}")  # Minimal resume

    permissions = AgentPermissions(read_outboxes=[], tools=[])
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


def test_credits_save_frequency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that credits are saved O(1) times per tick."""
    # Setup 3 agents
    agents = [_make_agent(tmp_path, f"agent_{i}") for i in range(3)]

    # Mock discover_agents to return these agents
    monkeypatch.setattr("lemming.engine.discover_agents", lambda base_path: agents)

    # Mock call_llm to avoid network and return empty action
    monkeypatch.setattr(
        "lemming.engine.call_llm",
        lambda *_, **__: json.dumps({"notes": "Done"}),
    )

    # Setup credits.json and org_config.json
    config_dir = tmp_path / "lemming" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "credits.json").write_text("{}")
    (config_dir / "org_config.json").write_text("{}")

    # Reset caches to ensure we load from our tmp_path
    org.reset_caches()

    # Spy on save_credits
    real_save_credits = org.save_credits
    save_credits_mock = MagicMock(side_effect=real_save_credits)

    # Patch where it is defined
    monkeypatch.setattr("lemming.org.save_credits", save_credits_mock)
    # Patch where it is imported in engine
    monkeypatch.setattr("lemming.engine.save_credits", save_credits_mock)

    # Run tick
    run_tick(tmp_path, tick=1)

    # It should be called exactly once (batch save at end of run_tick)
    # Agents run with persist_credits=False.
    assert save_credits_mock.call_count == 1


def test_credits_save_on_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that credits are saved even if an agent raises an exception."""
    # Setup agents
    agents = [_make_agent(tmp_path, "agent_1")]
    monkeypatch.setattr("lemming.engine.discover_agents", lambda base_path: agents)

    # Mock call_llm to raise exception
    monkeypatch.setattr("lemming.engine.call_llm", MagicMock(side_effect=Exception("LLM Boom")))

    # Setup config
    config_dir = tmp_path / "lemming" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "credits.json").write_text("{}")
    (config_dir / "org_config.json").write_text("{}")
    org.reset_caches()

    # Spy save_credits
    save_credits_mock = MagicMock()
    monkeypatch.setattr("lemming.org.save_credits", save_credits_mock)
    monkeypatch.setattr("lemming.engine.save_credits", save_credits_mock)

    # Run tick
    with pytest.raises(Exception, match="LLM Boom"):
        run_tick(tmp_path, tick=1)

    # verify save_credits was called
    assert save_credits_mock.call_count == 1
