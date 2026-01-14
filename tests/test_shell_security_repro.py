from lemming.tools import ShellTool
import os
from pathlib import Path
import tempfile
import pytest

def test_shell_tool_vulnerabilities(tmp_path):
    """Demonstrate vulnerabilities in ShellTool path validation."""
    base_path = tmp_path / "lemming"
    agents_dir = base_path / "agents"
    agent_name = "tester"
    agent_dir = agents_dir / agent_name
    workspace = agent_dir / "workspace"
    workspace.mkdir(parents=True)

    tool = ShellTool()

    print("--- Testing /.dockerenv (Vulnerability 1) ---")
    command = "cat /.dockerenv"
    result = tool.execute(agent_name=agent_name, base_path=base_path, command=command)

    # Assert that it is BLOCKED by our security check
    assert not result.success
    assert "Security violation" in result.error
    assert "absolute path" in result.error
    print("SECURE: Blocked access to /.dockerenv")

    print("\n--- Testing / (Vulnerability 2) ---")
    command = "ls /"
    result = tool.execute(agent_name=agent_name, base_path=base_path, command=command)

    # Assert that it is BLOCKED by our security check
    assert not result.success
    assert "Security violation" in result.error
    assert "absolute path" in result.error
    print("SECURE: Blocked access to /")

    print("\n--- Testing subdir/file.txt (Bug) ---")
    (workspace / "subdir").mkdir()
    (workspace / "subdir" / "file.txt").write_text("content", encoding="utf-8")

    command = "cat subdir/file.txt"
    result = tool.execute(agent_name=agent_name, base_path=base_path, command=command)

    # Assert that it ALLOWED
    assert result.success
    assert result.output == "content"
    print("WORKING: Allowed valid relative path")

if __name__ == "__main__":
    import shutil
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        test_shell_tool_vulnerabilities(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir)
