import json
from pathlib import Path
from unittest.mock import patch

import pytest

from lemming.engine import run_tick


def _create_dummy_agent(base_path: Path, name: str) -> None:
    agent_dir = base_path / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)

    resume_data = {
        "name": name,
        "title": f"Title for {name}",
        "short_description": "desc",
        "instructions": "instruct",
        "model": {"key": "gpt-4.1-mini", "temperature": 0.2, "max_tokens": 100},
        "permissions": {"read_outboxes": [], "tools": []},
        "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},
        "credits": {"max_credits": 10.0, "soft_cap": 5.0},
    }

    (agent_dir / "resume.json").write_text(json.dumps(resume_data))

    # Ensure credits exist
    config_dir = base_path / "lemming" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    credits_path = config_dir / "credits.json"
    if not credits_path.exists():
        credits_path.write_text("{}")

    credits = json.loads(credits_path.read_text())
    credits[name] = {
        "model": "gpt-4.1-mini",
        "cost_per_action": 0.01,
        "credits_left": 10.0,
        "max_credits": 10.0,
        "soft_cap": 5.0,
    }
    credits_path.write_text(json.dumps(credits))


def test_credits_io_reduction(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Setup
    base_path = tmp_path
    _create_dummy_agent(base_path, "agent1")
    _create_dummy_agent(base_path, "agent2")
    _create_dummy_agent(base_path, "agent3")

    # Ensure org config exists
    (base_path / "lemming" / "config").mkdir(parents=True, exist_ok=True)
    (base_path / "lemming" / "config" / "org_config.json").write_text("{}")

    # Mock LLM to avoid calls and return simple response
    monkeypatch.setattr("lemming.engine.call_llm", lambda *_, **__: json.dumps({"notes": "done"}))

    # We want to count calls to save_credits
    # We need to patch both places where it is used/imported

    with patch("lemming.org.save_credits") as mock_save_org, patch("lemming.engine.save_credits") as mock_save_engine:
        # Run tick
        run_tick(base_path, 1)

        # Verify optimization:
        # 1. deduct_credits (called by run_agent) should NOT persist (persist=False),
        #    so mock_save_org should be called 0 times.
        # 2. run_tick should call save_credits (imported in engine) EXACTLY ONCE at the end.

        assert mock_save_org.call_count == 0
        assert mock_save_engine.call_count == 1
