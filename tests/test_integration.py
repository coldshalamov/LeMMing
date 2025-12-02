import json
from pathlib import Path
from unittest.mock import patch

from lemming.agents import discover_agents, load_agent
from lemming.engine import run_tick, should_run
from lemming.messages import read_outbox_entries


def setup_org(tmp_path: Path) -> Path:
    config_dir = tmp_path / "lemming" / "config"
    config_dir.mkdir(parents=True)

    (config_dir / "org_config.json").write_text(
        json.dumps({"base_turn_seconds": 1, "max_turns": None}), encoding="utf-8"
    )
    (config_dir / "models.json").write_text(
        json.dumps({"test-model": {"provider": "openai", "model_name": "gpt-4.1-mini"}}),
        encoding="utf-8",
    )
    (config_dir / "credits.json").write_text(
        json.dumps({"agent_a": {"model": "test-model", "cost_per_action": 0.01, "credits_left": 10.0}}),
        encoding="utf-8",
    )

    agent_dir = tmp_path / "agents" / "agent_a"
    agent_dir.mkdir(parents=True)
    resume = {
        "name": "agent_a",
        "title": "Agent A",
        "short_description": "Test agent",
        "model": {"key": "test-model"},
        "permissions": {"read_outboxes": [], "tools": []},
        "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},
        "instructions": "Test agent instructions",
    }
    (agent_dir / "resume.json").write_text(json.dumps(resume), encoding="utf-8")
    return tmp_path


def test_agent_discovery(tmp_path: Path) -> None:
    base = setup_org(tmp_path)
    agents = discover_agents(base)
    assert len(agents) == 1
    assert agents[0].name == "agent_a"


def test_scheduling(tmp_path: Path) -> None:
    base = setup_org(tmp_path)
    agent = load_agent(base, "agent_a")
    assert should_run(agent, 1)
    assert should_run(agent, 2)
    agent.schedule.run_every_n_ticks = 2
    assert not should_run(agent, 1)
    assert should_run(agent, 2)


@patch("lemming.engine.call_llm")
def test_tick_produces_outbox(mock_llm, tmp_path: Path) -> None:
    base = setup_org(tmp_path)
    mock_llm.return_value = json.dumps(
        {
            "outbox_entries": [{"kind": "message", "payload": {"text": "hello"}}],
            "notes": "done",
        }
    )
    run_tick(base, 1)
    entries = read_outbox_entries(base, "agent_a")
    assert len(entries) == 1
    assert entries[0].payload["text"] == "hello"
