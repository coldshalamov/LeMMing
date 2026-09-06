import sys
import subprocess
from pathlib import Path
import pytest
import os

RUNNER_SCRIPT = """
import sys
from pathlib import Path
from lemming.tools import ShellTool

# Get base path from args
if len(sys.argv) > 1:
    base_path = Path(sys.argv[1]).resolve()
else:
    base_path = Path(".").resolve()

agent_name = "test_stdin_agent"
# We need to ensure directories exist for ShellTool to work
# ShellTool expects base_path/agents/agent_name/workspace
agent_dir = base_path / "agents" / agent_name
workspace_dir = agent_dir / "workspace"
workspace_dir.mkdir(parents=True, exist_ok=True)

tool = ShellTool()
# Execute cat
result = tool.execute(agent_name, base_path, command="cat")

# Print output
print(result.output, end="")
"""

def test_shell_tool_stdin_isolation(tmp_path):
    """
    Verify that ShellTool does not inherit stdin from the parent process.
    If it inherits, 'cat' will read the input we pipe to the runner script.
    If it is isolated (DEVNULL), 'cat' will read nothing (EOF).
    """

    # Create the runner script
    runner_path = tmp_path / "runner.py"
    runner_path.write_text(RUNNER_SCRIPT, encoding="utf-8")

    # Run the runner script with input piped to stdin
    # We use the current python executable
    input_str = "SECRET_DATA_SHOULD_NOT_BE_READ"

    # We need to set PYTHONPATH to include current directory so lemming can be imported
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    # Pass tmp_path to the runner so it creates files there instead of repo root
    proc = subprocess.run(
        [sys.executable, str(runner_path), str(tmp_path)],
        input=input_str,
        capture_output=True,
        text=True,
        cwd=os.getcwd(),
        env=env,
        timeout=5
    )

    if proc.returncode != 0:
        pytest.fail(f"Runner script failed: {proc.stderr}")

    output = proc.stdout

    # If vulnerable, output will contain SECRET_DATA_SHOULD_NOT_BE_READ
    assert input_str not in output, "ShellTool leaked stdin content to the command!"
