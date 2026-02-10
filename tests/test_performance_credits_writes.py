from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lemming import engine, org
from lemming.agents import Agent, AgentCredits, AgentModel, AgentPermissions, AgentSchedule


def create_mock_agents(n=5):
    agents = []
    for i in range(n):
        agent = Agent(
            name=f"agent_{i}",
            path=Path(f"/tmp/agents/agent_{i}"),
            title=f"Agent {i}",
            short_description="Test agent",
            workflow_description="Test",
            model=AgentModel(key="cli-mock", temperature=0.2, max_tokens=100),
            permissions=AgentPermissions(read_outboxes=[], tools=[]),
            schedule=AgentSchedule(run_every_n_ticks=1, phase_offset=0),
            resume_path=Path(f"/tmp/agents/agent_{i}/resume.json"),
            instructions="Test",
            credits=AgentCredits(max_credits=100.0, soft_cap=50.0),
        )
        agents.append(agent)
    return agents


def test_optimized_credit_writes(tmp_path):
    # Setup mocks
    base_path = tmp_path

    # Mock credits.json existence
    config_dir = base_path / "lemming" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "credits.json").write_text("{}")
    (config_dir / "org_config.json").write_text("{}")

    # Mock discover_agents to return 5 agents
    agents = create_mock_agents(5)

    # Mock LLM call to succeed
    mock_llm_response = '{"notes": "done", "outbox_entries": [], "tool_calls": [], "memory_updates": []}'

    # Create a shared mock for save_credits
    mock_save_credits = MagicMock()

    with (
        patch("lemming.engine.discover_agents", return_value=agents),
        patch("lemming.engine.call_llm", return_value=mock_llm_response),
        patch("lemming.engine.get_org_config", return_value={}),
        patch("lemming.engine.cleanup_old_outbox_entries", return_value=0),
        patch("lemming.engine.write_outbox_entry"),
        patch("lemming.engine.log_agent_action"),
        patch("lemming.engine.log_engine_event"),
        patch("lemming.org.save_credits", mock_save_credits),
        patch("lemming.engine.save_credits", mock_save_credits),
    ):

        org.reset_caches()

        engine.run_tick(base_path, 1)

        # Verify save_credits call count
        print(f"save_credits call count: {mock_save_credits.call_count}")

        # We expect exactly 1 call (batched at the end of tick)
        assert mock_save_credits.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__])
