from lemming.tools import FileReadTool, FileWriteTool, MemoryWriteTool


def test_file_read_limit(tmp_path):
    tool = FileReadTool()

    # Setup agent workspace
    agent_name = "test_agent"
    workspace = tmp_path / "agents" / agent_name / "workspace"
    workspace.mkdir(parents=True)

    # Create a large file (6MB), limit should be 5MB
    large_file = workspace / "large_log.txt"
    # Create sparse file or just write actual bytes.
    # Writing 6MB is fast enough.
    size_mb = 6
    content = "a" * (size_mb * 1024 * 1024)
    large_file.write_text(content)

    # Attempt to read
    result = tool.execute(agent_name=agent_name, base_path=tmp_path, path="large_log.txt")

    # Expect failure due to size limit
    assert not result.success, "File read should have failed due to size limit"
    assert "too large" in result.error.lower(), f"Unexpected error message: {result.error}"
    assert "max size is" in result.error.lower()


def test_file_write_limit(tmp_path):
    tool = FileWriteTool()

    # Create a dummy agent workspace
    agent_name = "test_agent"
    workspace = tmp_path / "agents" / agent_name / "workspace"
    workspace.mkdir(parents=True)

    # Try to write a file slightly larger than the limit
    # Limit is 100KB = 102400 bytes
    large_content = "a" * (102400 + 1)

    result = tool.execute(agent_name=agent_name, base_path=tmp_path, path="large_file.txt", content=large_content)

    assert not result.success
    assert "content too large" in result.error.lower()
    assert not (workspace / "large_file.txt").exists()


def test_file_write_within_limit(tmp_path):
    tool = FileWriteTool()
    agent_name = "test_agent"
    workspace = tmp_path / "agents" / agent_name / "workspace"
    workspace.mkdir(parents=True)

    content = "a" * 102400  # Exact limit

    result = tool.execute(agent_name=agent_name, base_path=tmp_path, path="ok_file.txt", content=content)

    assert result.success
    assert (workspace / "ok_file.txt").exists()


def test_memory_write_limit(tmp_path):
    tool = MemoryWriteTool()
    agent_name = "test_agent"

    # Limit is 50KB = 51200 bytes
    # Create a large object
    large_value = {"data": "a" * 52000}

    result = tool.execute(agent_name=agent_name, base_path=tmp_path, key="large_mem", value=large_value)

    assert not result.success
    assert "memory value too large" in result.error.lower()

    # Verify file not created
    mem_path = tmp_path / "agents" / agent_name / "memory" / "large_mem.json"
    assert not mem_path.exists()


def test_memory_write_within_limit(tmp_path):
    tool = MemoryWriteTool()
    agent_name = "test_agent"

    value = {"data": "small"}

    result = tool.execute(agent_name=agent_name, base_path=tmp_path, key="small_mem", value=value)

    assert result.success
    mem_path = tmp_path / "agents" / agent_name / "memory" / "small_mem.json"
    assert mem_path.exists()
    assert not result.error
