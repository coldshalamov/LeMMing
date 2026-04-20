import json
from pathlib import Path
from unittest.mock import patch

from lemming.engine import run_tick
from lemming.messages import OutboxEntry, write_outbox_entry


def setup_org(tmp_path: Path):
    config_dir = tmp_path / "lemming" / "config"
    config_dir.mkdir(parents=True)

    # Configure max_outbox_age_ticks to 10
    (config_dir / "org_config.json").write_text(
        json.dumps({"base_turn_seconds": 1, "max_turns": None, "max_outbox_age_ticks": 10}), encoding="utf-8"
    )
    # Dummy models
    (config_dir / "models.json").write_text(
        json.dumps({"test-model": {"provider": "openai", "model_name": "gpt-4.1-mini"}}),
        encoding="utf-8",
    )
    # Dummy credits
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
        "schedule": {"run_every_n_ticks": 100, "phase_offset": 0},  # Don't run often
        "instructions": "Test agent instructions",
    }
    (agent_dir / "resume.json").write_text(json.dumps(resume), encoding="utf-8")
    (agent_dir / "outbox").mkdir()
    return tmp_path


@patch("lemming.engine.call_llm")
def test_outbox_cleanup_throttling(mock_llm, tmp_path: Path):
    base_path = setup_org(tmp_path)

    # Create an old entry at tick 5.
    # Max age is 10. So it should be deleted at tick > 15.
    entry = OutboxEntry.create(agent="agent_a", tick=5, kind="msg", payload={"text": "old"})
    entry_path = write_outbox_entry(base_path, "agent_a", entry)

    assert entry_path.exists()

    # Run tick 21 (not divisible by 10).
    # Even though 21 - 5 = 16 > 10, cleanup should be skipped if optimization is in place.
    # Note: On unoptimized code, this will fail because cleanup runs every tick.
    run_tick(base_path, 21)

    # Verify file still exists (cleanup throttled)
    assert entry_path.exists(), "Cleanup should be skipped on ticks not divisible by 10"

    # Run tick 30 (divisible by 10).
    # 30 - 5 = 25 > 10. Cleanup should happen.
    run_tick(base_path, 30)

    # Verify file is deleted
    assert not entry_path.exists(), "Cleanup should run on ticks divisible by 10"
