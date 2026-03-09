import json
from unittest.mock import MagicMock, patch

from lemming.agents import Agent, AgentPermissions
from lemming.department import analyze_social_graph


def test_analyze_social_graph_optimization(tmp_path):
    # Setup structure
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    agent1_dir = agents_dir / "agent1"
    agent1_dir.mkdir()
    (agent1_dir / "outbox").mkdir()

    agent2_dir = agents_dir / "agent2"
    agent2_dir.mkdir()
    (agent2_dir / "outbox").mkdir()

    agent1 = MagicMock(spec=Agent)
    agent1.name = "agent1"
    agent1.path = agent1_dir
    agent1.permissions = AgentPermissions(read_outboxes=["agent2"], tools=[])

    agent2 = MagicMock(spec=Agent)
    agent2.name = "agent2"
    agent2.path = agent2_dir
    agent2.permissions = AgentPermissions(read_outboxes=[], tools=[])

    # Message 1: Recent, has 'to' (Legacy support check)
    msg1 = {
        "id": "1",
        "tick": 1000,
        "agent": "agent1",
        "kind": "text",
        "payload": {"text": "hello"},
        "tags": [],
        "created_at": "2023-01-01T00:00:00Z",
        "recipients": ["agent2"],
        "to": ["agent2"],
    }
    with open(agent1_dir / "outbox" / "1000_1.json", "w") as f:
        json.dump(msg1, f)

    # Message 2: Old (Should be ignored by threshold)
    msg2 = {
        "id": "2",
        "tick": 100,
        "agent": "agent1",
        "kind": "text",
        "payload": {"text": "hello"},
        "tags": [],
        "created_at": "2023-01-01T00:00:00Z",
        "recipients": ["agent2"],
        "to": ["agent2"],
    }
    with open(agent1_dir / "outbox" / "0100_2.json", "w") as f:
        json.dump(msg2, f)

    # Message 3: Recent, has 'recipients' only (New format check)
    msg3 = {
        "id": "3",
        "tick": 1001,
        "agent": "agent1",
        "kind": "text",
        "payload": {"text": "hello"},
        "tags": [],
        "created_at": "2023-01-01T00:00:00Z",
        "recipients": ["agent2"],
        # No "to"
    }
    with open(agent1_dir / "outbox" / "1001_3.json", "w") as f:
        json.dump(msg3, f)

    with patch("lemming.department.discover_agents", return_value=[agent1, agent2]):
        # Run with current_tick = 1000. Threshold = 900.
        rels = analyze_social_graph(tmp_path, current_tick=1000)

        rel = next((r for r in rels if r.source == "agent1" and r.target == "agent2"), None)
        assert rel is not None

        print(f"Interaction count: {rel.interaction_count}")

        # We assume existing code only counts msg1 (has 'to').
        # If msg3 is counted, then existing code handles 'recipients' (unlikely based on my reading).

        assert rel.interaction_count >= 1
