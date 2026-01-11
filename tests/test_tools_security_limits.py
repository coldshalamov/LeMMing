
import pytest
import json
from lemming.tools import FileWriteTool, MemoryWriteTool

def test_file_write_limit(tmp_path):
    base_path = tmp_path
    agents_dir = base_path / "agents"
    agent_name = "test_agent"
    workspace = agents_dir / agent_name / "workspace"
    workspace.mkdir(parents=True)

    tool = FileWriteTool()

    # Create large content (1MB)
    large_content = "x" * (1024 * 1024)

    result = tool.execute(
        agent_name=agent_name,
        base_path=base_path,
        path="large_file.txt",
        content=large_content
    )

    assert not result.success
    assert "too large" in result.error.lower()
    assert not (workspace / "large_file.txt").exists()

def test_memory_write_limit(tmp_path):
    base_path = tmp_path
    agents_dir = base_path / "agents"
    agent_name = "test_agent"
    memory_dir = agents_dir / agent_name / "memory"
    memory_dir.mkdir(parents=True)

    tool = MemoryWriteTool()

    # Create large content (1MB)
    large_content = {"data": "x" * (1024 * 1024)}

    result = tool.execute(
        agent_name=agent_name,
        base_path=base_path,
        key="large_memory",
        value=large_content
    )

    assert not result.success
    assert "too large" in result.error.lower()
    assert not (memory_dir / "large_memory.json").exists()
