import json
from pathlib import Path

from lemming.agents import load_agent, validate_resume


def test_load_from_json_resume(tmp_path: Path) -> None:
    agent_dir = tmp_path / "agents" / "test_agent"
    agent_dir.mkdir(parents=True)
    resume = {
        "name": "test_agent",
        "title": "Test Agent",
        "short_description": "A test agent",
        "model": {"key": "gpt-4.1-mini"},
        "permissions": {"read_outboxes": ["*"], "tools": ["memory_read"]},
        "schedule": {"run_every_n_ticks": 2, "phase_offset": 0},
        "instructions": "Test instructions",
    }
    with (agent_dir / "resume.json").open("w", encoding="utf-8") as f:
        json.dump(resume, f)

    agent = load_agent(tmp_path, "test_agent")
    assert agent.name == "test_agent"
    assert agent.title == "Test Agent"
    assert agent.model.key == "gpt-4.1-mini"
    assert agent.schedule.run_every_n_ticks == 2
    assert agent.permissions.read_outboxes == ["*"]


def test_validate_resume_missing_fields(tmp_path: Path) -> None:
    agent_dir = tmp_path / "agents" / "bad_agent"
    agent_dir.mkdir(parents=True)
    resume_path = agent_dir / "resume.json"
    resume_path.write_text(json.dumps({"name": "bad_agent", "title": "Bad"}), encoding="utf-8")

    errors = validate_resume(resume_path)
    assert errors
    assert any("permissions" in err for err in errors)
