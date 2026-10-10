from lemming.tools import ShellTool
from pathlib import Path
import os
import pytest

@pytest.mark.skipif(os.name == 'nt', reason="Relies on Unix commands not available as executables on Windows")
def test_shell_tool_env_leak(tmp_path):
    """Ensure ShellTool does not leak sensitive environment variables to the subprocess."""
    base_path = tmp_path / "lemming"
    agents_dir = base_path / "agents"
    agent_name = "tester"
    agent_dir = agents_dir / agent_name
    workspace = agent_dir / "workspace"
    workspace.mkdir(parents=True)

    tool = ShellTool()

    # Set a sensitive environment variable
    os.environ["SECRET_API_KEY"] = "super_secret_value"

    try:
        # jq is an allowed command and can dump environment variables
        command = "jq -n env"
        result = tool.execute(agent_name=agent_name, base_path=base_path, command=command)

        # Assert that the sensitive variable is NOT in the output
        if result.success:
            assert "super_secret_value" not in result.output, "ShellTool leaked sensitive environment variables!"
    finally:
        # Cleanup
        if "SECRET_API_KEY" in os.environ:
            del os.environ["SECRET_API_KEY"]
