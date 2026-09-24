from pathlib import Path
from unittest.mock import MagicMock, patch

from lemming.providers import CLIProvider
from lemming.tools import ShellTool


def test_cli_provider_env_leak(monkeypatch):
    monkeypatch.setenv("SECRET_API_KEY", "supersecret")
    provider = CLIProvider(command=["env"])

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        provider.call(model_name="test", messages=[])

        args, kwargs = mock_run.call_args
        env_passed = kwargs.get("env")
        assert env_passed is not None
        assert "SECRET_API_KEY" not in env_passed


def test_shell_tool_env_leak(monkeypatch):
    monkeypatch.setenv("SECRET_API_KEY", "supersecret")
    tool = ShellTool()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        tool.execute(agent_name="test", base_path=Path("."), command="ls")

        args, kwargs = mock_run.call_args
        env_passed = kwargs.get("env")
        assert env_passed is not None
        assert "SECRET_API_KEY" not in env_passed
