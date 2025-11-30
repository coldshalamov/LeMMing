"""Tests for agents module."""

from __future__ import annotations

import pytest

from lemming.agents import Agent, bootstrap_agent_from_template, discover_agents, load_agent, parse_resume


def test_parse_resume(setup_agent_dirs, temp_base_path):
    """Test parsing a resume file."""
    resume_path = temp_base_path / "agents" / "manager" / "resume.txt"
    parsed = parse_resume(resume_path)

    assert parsed["name"] == "MANAGER"
    assert "role" in parsed
    assert "description" in parsed
    assert parsed["instructions_text"] != ""
    assert isinstance(parsed["config_json"], dict)
    assert parsed["config_json"]["model"] == "gpt-4.1-mini"


def test_load_agent(setup_agent_dirs, temp_base_path):
    """Test loading an agent."""
    agent = load_agent(temp_base_path, "manager")

    assert isinstance(agent, Agent)
    assert agent.name == "manager"
    assert agent.model_key == "gpt-4.1-mini"
    assert agent.org_speed_multiplier == 1
    assert agent.max_credits == 100.0
    assert agent.path == temp_base_path / "agents" / "manager"


def test_load_agent_missing_resume(temp_base_path):
    """Test loading agent with missing resume."""
    agents_dir = temp_base_path / "agents" / "nonexistent"
    agents_dir.mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match="Missing resume"):
        load_agent(temp_base_path, "nonexistent")


def test_discover_agents(setup_agent_dirs, temp_base_path):
    """Test discovering all agents."""
    agents = discover_agents(temp_base_path)

    assert len(agents) == 3  # manager, planner, hr
    agent_names = {a.name for a in agents}
    assert "manager" in agent_names
    assert "planner" in agent_names
    assert "hr" in agent_names


def test_discover_agents_empty(temp_base_path):
    """Test discovering agents when none exist."""
    agents = discover_agents(temp_base_path)
    assert len(agents) == 0


def test_discover_agents_skips_template(setup_agent_dirs, temp_base_path):
    """Test that agent_template is skipped during discovery."""
    # Create agent_template directory
    template_dir = temp_base_path / "agents" / "agent_template"
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "resume.txt").write_text(
        "Name: TEMPLATE\nRole: Template\nDescription: Template\n[INSTRUCTIONS]\nTest\n[CONFIG]\n{}"
    )

    agents = discover_agents(temp_base_path)
    agent_names = {a.name for a in agents}
    assert "agent_template" not in agent_names


def test_bootstrap_agent_from_template(temp_base_path):
    """Test bootstrapping a new agent from template."""
    # Create template
    template_dir = temp_base_path / "agents" / "agent_template"
    template_dir.mkdir(parents=True)
    template_resume = """Name: TEMPLATE_AGENT
Role: Generic worker agent
Description: A generic LeMMing agent created from the template.

[INSTRUCTIONS]
You are a LeMMing agent. Follow your role description.

[CONFIG]
{
  "model": "gpt-4.1-mini",
  "org_speed_multiplier": 1,
  "send_to": [],
  "read_from": [],
  "max_credits": 50.0
}
"""
    (template_dir / "resume.txt").write_text(template_resume)

    # Bootstrap new agent
    role_config = {
        "name": "TESTER",
        "role": "Testing agent",
        "description": "Runs tests and reports results",
        "config": {
            "model": "gpt-4.1",
            "org_speed_multiplier": 2,
            "send_to": ["manager"],
            "read_from": ["manager"],
            "max_credits": 200.0,
        },
    }

    agent = bootstrap_agent_from_template(temp_base_path, "tester", role_config)

    assert agent.name == "tester"
    assert agent.model_key == "gpt-4.1"
    assert agent.org_speed_multiplier == 2
    assert agent.max_credits == 200.0

    # Verify resume was created
    resume_path = temp_base_path / "agents" / "tester" / "resume.txt"
    assert resume_path.exists()

    # Verify directories were created
    for subdir in ["outbox", "memory", "logs", "config"]:
        assert (temp_base_path / "agents" / "tester" / subdir).exists()


def test_bootstrap_agent_no_template(temp_base_path):
    """Test bootstrapping without template fails."""
    with pytest.raises(FileNotFoundError, match="Template resume not found"):
        bootstrap_agent_from_template(temp_base_path, "tester", {})


def test_agent_dataclass_fields(setup_agent_dirs, temp_base_path):
    """Test that Agent dataclass has all expected fields."""
    agent = load_agent(temp_base_path, "manager")

    assert hasattr(agent, "name")
    assert hasattr(agent, "path")
    assert hasattr(agent, "model_key")
    assert hasattr(agent, "org_speed_multiplier")
    assert hasattr(agent, "send_to")
    assert hasattr(agent, "read_from")
    assert hasattr(agent, "max_credits")
    assert hasattr(agent, "resume_text")
    assert hasattr(agent, "instructions_text")
    assert hasattr(agent, "config_json")
    assert hasattr(agent, "role")
    assert hasattr(agent, "description")


def test_parse_resume_complex_instructions(temp_base_path):
    """Test parsing resume with complex instructions."""
    resume = """Name: COMPLEX
Role: Complex agent
Description: Has complex instructions

[INSTRUCTIONS]
You are a complex agent.

Instructions:
1. Do this
2. Do that
3. Do something else

Always output JSON:
{
  "messages": [],
  "notes": "test"
}

[CONFIG]
{
  "model": "gpt-4.1-mini",
  "org_speed_multiplier": 1,
  "send_to": ["manager"],
  "read_from": ["manager"],
  "max_credits": 100.0
}
"""
    resume_path = temp_base_path / "test_resume.txt"
    resume_path.write_text(resume)

    parsed = parse_resume(resume_path)
    assert "Always output JSON" in parsed["instructions_text"]
    assert "Do this" in parsed["instructions_text"]
