from unittest.mock import MagicMock, patch

from lemming import agents, engine


def test_credits_persistence_efficiency(tmp_path):
    # Setup
    base_path = tmp_path
    (base_path / "lemming" / "config").mkdir(parents=True)
    (base_path / "lemming" / "config" / "org_config.json").write_text("{}", encoding="utf-8")
    (base_path / "lemming" / "config" / "credits.json").write_text("{}", encoding="utf-8")

    # Mock agents
    agent1 = MagicMock(spec=agents.Agent)
    agent1.name = "agent1"
    agent1.title = "Agent 1"
    agent1.short_description = "Description 1"
    agent1.workflow_description = "Workflow 1"
    agent1.schedule = MagicMock()
    agent1.schedule.run_every_n_ticks = 1
    agent1.schedule.phase_offset = 0
    agent1.model = MagicMock()
    agent1.model.key = "gpt-4o-mini"
    agent1.model.temperature = 0.2
    agent1.permissions = MagicMock()
    agent1.permissions.tools = []
    agent1.permissions.read_outboxes = []
    agent1.instructions = "instruction"
    agent1.credits = agents.AgentCredits(max_credits=100.0, soft_cap=50.0)
    agent1.path = base_path / "agents" / "agent1"

    agent2 = MagicMock(spec=agents.Agent)
    agent2.name = "agent2"
    agent2.title = "Agent 2"
    agent2.short_description = "Description 2"
    agent2.workflow_description = "Workflow 2"
    agent2.schedule = MagicMock()
    agent2.schedule.run_every_n_ticks = 1
    agent2.schedule.phase_offset = 0
    agent2.model = MagicMock()
    agent2.model.key = "gpt-4o-mini"
    agent2.model.temperature = 0.2
    agent2.permissions = MagicMock()
    agent2.permissions.tools = []
    agent2.permissions.read_outboxes = []
    agent2.instructions = "instruction"
    agent2.credits = agents.AgentCredits(max_credits=100.0, soft_cap=50.0)
    agent2.path = base_path / "agents" / "agent2"

    # Mock discover_agents to return 2 agents
    with patch("lemming.engine.discover_agents", return_value=[agent1, agent2]):
        # Mock LLM call to return valid JSON
        with patch(
            "lemming.engine.call_llm",
            return_value='{"outbox_entries": [], "tool_calls": [], "memory_updates": [], "notes": "note"}',
        ):
            # Mock save_credits in BOTH engine and org to catch all calls
            mock_save_credits = MagicMock()
            with (
                patch("lemming.org.save_credits", mock_save_credits),
                patch("lemming.engine.save_credits", mock_save_credits),
            ):

                # Mock cleanup to avoid errors
                with patch("lemming.engine.cleanup_old_outbox_entries"):
                    # Mock persist_tick
                    with patch("lemming.engine.persist_tick"):
                        # Mock load_tick
                        with patch("lemming.engine.load_tick", return_value=1):
                            # Mock get_memory_context to avoid errors
                            with patch("lemming.engine.get_memory_context", return_value=""):
                                # Mock collect_readable_outboxes
                                with patch("lemming.engine.collect_readable_outboxes", return_value=[]):
                                    # Mock get_credits to return valid credits
                                    with patch(
                                        "lemming.org.get_credits",
                                        return_value={"agent1": {"credits_left": 100}, "agent2": {"credits_left": 100}},
                                    ):
                                        # Run tick
                                        engine.run_tick(base_path, 1)

                                        # Expect save_credits to be called ONCE (batch save)
                                        assert mock_save_credits.call_count == 1
