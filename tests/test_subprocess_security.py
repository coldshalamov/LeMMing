import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from lemming.providers import CLIProvider
from lemming.tools import ShellTool


def test_cli_provider_env_sanitization():
    provider = CLIProvider(command=["echo"], env={"CUSTOM_TOKEN": "safe"})

    with patch.dict(os.environ, {"OPENAI_API_KEY": "secret1", "GITHUB_TOKEN": "secret2", "NORMAL_VAR": "value"}):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="mock output", stderr="", returncode=0)

            provider.call(model_name="echo", messages=[{"role": "user", "content": "hello"}])

            mock_run.assert_called_once()
            called_env = mock_run.call_args[1]["env"]
            assert "OPENAI_API_KEY" not in called_env
            assert "GITHUB_TOKEN" not in called_env
            assert called_env.get("NORMAL_VAR") == "value"
            assert called_env.get("CUSTOM_TOKEN") == "safe"


def test_shell_tool_env_sanitization():
    tool = ShellTool()

    with patch.dict(os.environ, {"OPENAI_API_KEY": "secret1", "GITHUB_TOKEN": "secret2", "NORMAL_VAR": "value"}):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="mock output", stderr="", returncode=0)

            tool.execute(agent_name="test_agent", base_path=Path("/tmp"), command="ls -la")

            mock_run.assert_called_once()
            called_env = mock_run.call_args[1]["env"]
            assert "OPENAI_API_KEY" not in called_env
            assert "GITHUB_TOKEN" not in called_env
            assert called_env.get("NORMAL_VAR") == "value"
