
import pytest
import json
from pathlib import Path
from lemming.tools import FileWriteTool, MemoryWriteTool

def test_file_write_limit(tmp_path):
    tool = FileWriteTool()

    # Create a dummy agent workspace
    agent_name = "test_agent"
    workspace = tmp_path / "agents" / agent_name / "workspace"
    workspace.mkdir(parents=True)

    # Try to write a file slightly larger than the limit
    # Limit is 100KB = 102400 bytes
    large_content = "a" * (102400 + 1)

    result = tool.execute(
        agent_name=agent_name,
        base_path=tmp_path,
        path="large_file.txt",
        content=large_content
    )

    assert not result.success
    assert "Content too large" in result.error
    assert not (workspace / "large_file.txt").exists()

def test_file_write_within_limit(tmp_path):
    tool = FileWriteTool()
    agent_name = "test_agent"
    workspace = tmp_path / "agents" / agent_name / "workspace"
    workspace.mkdir(parents=True)

    content = "a" * 102400 # Exact limit

    result = tool.execute(
        agent_name=agent_name,
        base_path=tmp_path,
        path="ok_file.txt",
        content=content
    )

    assert result.success
    assert (workspace / "ok_file.txt").exists()

def test_memory_write_limit(tmp_path):
    tool = MemoryWriteTool()
    agent_name = "test_agent"

    # Limit is 50KB = 51200 bytes
    # Create a large object
    large_value = {"data": "a" * 52000}

    result = tool.execute(
        agent_name=agent_name,
        base_path=tmp_path,
        key="large_mem",
        value=large_value
    )

    assert not result.success
    assert "Memory value too large" in result.error

    # Verify file not created
    mem_path = tmp_path / "agents" / agent_name / "memory" / "large_mem.json"
    assert not mem_path.exists()

def test_memory_write_within_limit(tmp_path):
    tool = MemoryWriteTool()
    agent_name = "test_agent"

    value = {"data": "small"}

    result = tool.execute(
        agent_name=agent_name,
        base_path=tmp_path,
        key="small_mem",
        value=value
    )

    assert result.success
    mem_path = tmp_path / "agents" / agent_name / "memory" / "small_mem.json"
    assert mem_path.exists()
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
