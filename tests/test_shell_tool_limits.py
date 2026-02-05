from lemming.tools import ShellTool, FileWriteTool
import pytest
import os

@pytest.mark.skipif(os.name == 'nt', reason="ShellTool only supports Unix commands (cat)")
def test_shell_output_limit(tmp_path):
    base_path = tmp_path / "lemming"
    agents_dir = base_path / "agents"
    agent_name = "tester"

    # Setup
    workspace = agents_dir / agent_name / "workspace"
    workspace.mkdir(parents=True)

    # 1. Create a large file (60KB)
    # FileWriteTool limit is 100KB, so 60KB is allowed.
    large_content = "a" * (60 * 1024)
    file_tool = FileWriteTool()
    result = file_tool.execute(
        agent_name=agent_name,
        base_path=base_path,
        path="large.txt",
        content=large_content
    )
    assert result.success, "Failed to create large file for testing"

    # 2. Cat the file using ShellTool
    shell_tool = ShellTool()
    if os.name == 'nt':
        command = "type large.txt"
    else:
        command = "cat large.txt"

    result = shell_tool.execute(
        agent_name=agent_name,
        base_path=base_path,
        command=command
    )

    # 3. Assert SECURE behavior: Failure and truncated output
    # This proves the fix works (enforces 50KB limit)
    assert not result.success
    assert "exceeded limit" in result.error
    assert len(result.output) <= 50 * 1024
