
import pytest
from lemming.tools import FileWriteTool, MemoryWriteTool, ToolResult

def test_file_write_limit(tmp_path):
    tool = FileWriteTool()
    base_path = tmp_path
    agent_name = "test_agent"
    (base_path / "agents" / agent_name / "workspace").mkdir(parents=True)

    # Test small write (OK)
    res = tool.execute(agent_name, base_path, path="small.txt", content="a" * 100)
    assert res.success

    # Test large write (Fail)
    res = tool.execute(agent_name, base_path, path="large.txt", content="a" * (100 * 1024 + 1))
    assert not res.success
    assert "Content too large" in res.error

def test_memory_write_limit(tmp_path):
    tool = MemoryWriteTool()
    base_path = tmp_path
    agent_name = "test_agent"
    (base_path / "agents" / agent_name / "memory").mkdir(parents=True)

    # Test small write (OK)
    res = tool.execute(agent_name, base_path, key="small", value={"a": "b"})
    assert res.success

    # Test large write (Fail)
    large_val = "a" * (50 * 1024 + 1)
    res = tool.execute(agent_name, base_path, key="large", value=large_val)
    assert not res.success
    assert "Memory value too large" in res.error
