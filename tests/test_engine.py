"""Integration tests for engine module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from lemming.engine import _agent_should_run, _build_prompt, _parse_llm_output, _run_agent, run_once


def test_build_prompt_no_messages(setup_agent_dirs, temp_base_path):
    """Test building prompt with no messages."""
    from lemming.agents import load_agent

    agent = load_agent(temp_base_path, "manager")
    prompt = _build_prompt(temp_base_path, agent, [])

    assert len(prompt) == 4
    assert prompt[0]["role"] == "system"
    assert "LeMMing agent" in prompt[0]["content"]
    assert prompt[1]["role"] == "system"
    assert prompt[2]["role"] == "user"
    assert "MEMORY CONTEXT" in prompt[2]["content"]
    assert prompt[3]["role"] == "user"
    assert "No new messages" in prompt[3]["content"]


def test_build_prompt_with_messages(setup_agent_dirs, temp_base_path):
    """Test building prompt with messages."""
    from lemming.agents import load_agent

    agent = load_agent(temp_base_path, "manager")
    messages = [
        {"sender": "planner", "receiver": "manager", "content": "Hello", "importance": "normal"},
        {"sender": "hr", "receiver": "manager", "content": "Update", "importance": "high"},
    ]
    prompt = _build_prompt(temp_base_path, agent, messages)

    assert len(prompt) == 4
    assert "Incoming messages:" in prompt[3]["content"]
    assert "From planner" in prompt[3]["content"]
    assert "From hr" in prompt[3]["content"]


def test_parse_llm_output_valid():
    """Test parsing valid JSON output."""
    json_str = '{"messages": [{"to": "planner", "content": "test"}], "notes": "Done"}'
    parsed = _parse_llm_output(json_str)

    assert parsed["messages"][0]["to"] == "planner"
    assert parsed["notes"] == "Done"


def test_parse_llm_output_invalid():
    """Test parsing invalid JSON output."""
    parsed = _parse_llm_output("This is not JSON")

    assert parsed["messages"] == []
    assert "Failed to parse" in parsed["notes"]


def test_agent_should_run_force():
    """Test agent should run when forced."""
    from lemming.agents import Agent

    agent = Agent(
        name="test",
        path=Path("/tmp/test"),
        model_key="gpt-4.1-mini",
        org_speed_multiplier=10,
        send_to=[],
        read_from=[],
        max_credits=100.0,
        resume_text="",
        instructions_text="",
        config_json={},
        role="test",
        description="test",
    )

    assert _agent_should_run(agent, current_turn=1, force=True) is True
    assert _agent_should_run(agent, current_turn=5, force=True) is True


def test_agent_should_run_by_multiplier():
    """Test agent should run based on speed multiplier."""
    from lemming.agents import Agent

    agent = Agent(
        name="test",
        path=Path("/tmp/test"),
        model_key="gpt-4.1-mini",
        org_speed_multiplier=3,
        send_to=[],
        read_from=[],
        max_credits=100.0,
        resume_text="",
        instructions_text="",
        config_json={},
        role="test",
        description="test",
    )

    assert _agent_should_run(agent, current_turn=3) is True
    assert _agent_should_run(agent, current_turn=6) is True
    assert _agent_should_run(agent, current_turn=9) is True
    assert _agent_should_run(agent, current_turn=1) is False
    assert _agent_should_run(agent, current_turn=2) is False


@patch("lemming.engine.call_llm")
def test_run_agent_success(mock_call_llm, temp_base_path, setup_config_files, setup_agent_dirs):
    """Test running an agent successfully."""
    from lemming.agents import load_agent

    mock_call_llm.return_value = '{"messages": [{"to": "planner", "content": "Task assigned"}], "notes": "Working"}'

    agent = load_agent(temp_base_path, "manager")
    result = _run_agent(temp_base_path, agent, current_turn=1, incoming_payloads=[])

    assert result["notes"] == "Working"
    assert len(result["messages"]) == 1
    mock_call_llm.assert_called_once()


@patch("lemming.engine.call_llm")
def test_run_agent_no_credits(mock_call_llm, temp_base_path, setup_config_files, setup_agent_dirs):
    """Test running agent with no credits."""
    from lemming.agents import load_agent
    from lemming.org import deduct_credits

    agent = load_agent(temp_base_path, "manager")

    # Drain credits
    deduct_credits("manager", 100.0, temp_base_path)

    result = _run_agent(temp_base_path, agent, current_turn=1, incoming_payloads=[])

    assert result == {}
    mock_call_llm.assert_not_called()


@patch("lemming.engine.call_llm")
def test_run_agent_sends_messages(mock_call_llm, temp_base_path, setup_config_files, setup_agent_dirs):
    """Test that agent sends messages to allowed recipients."""
    from lemming.agents import load_agent

    mock_call_llm.return_value = (
        '{"messages": [{"to": "planner", "content": "Hello", '
        '"importance": "normal", "ttl_turns": 10}], "notes": "Sent"}'
    )

    agent = load_agent(temp_base_path, "manager")
    _run_agent(temp_base_path, agent, current_turn=1, incoming_payloads=[])

    # Check that message was sent
    msg_dir = temp_base_path / "agents" / "manager" / "outbox" / "planner"
    assert msg_dir.exists()
    msg_files = list(msg_dir.glob("msg_*.json"))
    assert len(msg_files) == 1


@patch("lemming.engine.call_llm")
def test_run_agent_logs_notes(mock_call_llm, temp_base_path, setup_config_files, setup_agent_dirs):
    """Test that agent notes are logged."""
    from lemming.agents import load_agent

    mock_call_llm.return_value = '{"messages": [], "notes": "This is a test note"}'

    agent = load_agent(temp_base_path, "manager")
    _run_agent(temp_base_path, agent, current_turn=5, incoming_payloads=[])

    log_file = agent.path / "logs" / "activity.log"
    assert log_file.exists()

    log_content = log_file.read_text()
    assert "Turn 5: This is a test note" in log_content


@patch("lemming.engine.call_llm")
def test_run_once_integration(mock_call_llm, temp_base_path, setup_config_files, setup_agent_dirs):
    """Integration test for run_once."""
    mock_call_llm.return_value = '{"messages": [], "notes": "Turn completed"}'

    run_once(temp_base_path, current_turn=1)

    # Verify all agents ran
    mock_call_llm.assert_called()
    assert mock_call_llm.call_count == 3  # manager, planner, hr


@patch("lemming.engine.call_llm")
def test_run_once_manager_summary(mock_call_llm, temp_base_path, setup_config_files, setup_agent_dirs):
    """Test that manager summary is created."""
    mock_call_llm.return_value = '{"messages": [], "notes": "Summary for turn 12"}'

    # Turn 12 should trigger summary (summary_every_n_turns=12)
    run_once(temp_base_path, current_turn=12)

    # Check summary file exists
    summary_file = temp_base_path / "agents" / "manager" / "logs" / "summary_12.txt"
    assert summary_file.exists()
    assert "Summary for turn 12" in summary_file.read_text()


@patch("lemming.engine.call_llm")
def test_run_agent_deducts_credits(mock_call_llm, temp_base_path, setup_config_files, setup_agent_dirs):
    """Test that credits are deducted after running agent."""
    from lemming.agents import load_agent
    from lemming.org import get_agent_credits

    mock_call_llm.return_value = '{"messages": [], "notes": "Done"}'

    agent = load_agent(temp_base_path, "manager")
    initial_credits = get_agent_credits("manager", temp_base_path)["credits_left"]

    _run_agent(temp_base_path, agent, current_turn=1, incoming_payloads=[])

    final_credits = get_agent_credits("manager", temp_base_path)["credits_left"]
    assert final_credits < initial_credits
