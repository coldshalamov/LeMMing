from lemming.api import _read_agent_logs


def test_read_agent_logs_traversal_blocked(tmp_path):
    """Test that _read_agent_logs BLOCKS traversal."""
    base_path = tmp_path
    agents_dir = base_path / "agents"
    agents_dir.mkdir()

    # Create a structure that mimics traversal
    # If agent_name = "../", path = base_path/logs/structured.jsonl
    logs_dir = base_path / "logs"
    logs_dir.mkdir()
    target_file = logs_dir / "structured.jsonl"
    target_file.write_text('{"secret": "exposed"}')

    # Try traversal
    entries = _read_agent_logs(base_path, "..")

    # Should be empty list now because ".." is invalid agent name
    assert entries == []

    # Try another invalid name
    entries = _read_agent_logs(base_path, "../secret")
    assert entries == []

    # Try valid agent
    agent_dir = agents_dir / "valid_agent"
    agent_logs = agent_dir / "logs"
    agent_logs.mkdir(parents=True)
    (agent_logs / "structured.jsonl").write_text('{"msg": "ok"}')

    entries = _read_agent_logs(base_path, "valid_agent")
    assert len(entries) == 1
    assert entries[0]["msg"] == "ok"


if __name__ == "__main__":
    pass
