import os
from unittest.mock import MagicMock, patch

from lemming.providers import CLIProvider


def test_cli_provider_env_leak():
    """Verify that CLIProvider removes sensitive environment variables before running."""
    provider = CLIProvider(command=["echo"])

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="mock output", stderr="", returncode=0)

        # Set a sensitive env var
        os.environ["SUPER_SECRET_API_KEY"] = "12345"

        messages = [{"role": "user", "content": "test"}]
        provider.call(model_name="echo", messages=messages)

        mock_run.assert_called_once()
        run_env = mock_run.call_args[1].get("env", {})

        # Ensure it was removed
        assert "SUPER_SECRET_API_KEY" not in run_env

        # Cleanup
        os.environ.pop("SUPER_SECRET_API_KEY", None)


def test_cli_provider_explicit_env_allowed():
    """Verify that CLIProvider allows explicit env vars even if sensitive."""
    provider = CLIProvider(command=["echo"], env={"API_KEY": "allowed_explicit_key"})

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="mock output", stderr="", returncode=0)

        # Set a sensitive env var in system
        os.environ["SYSTEM_SECRET_API_KEY"] = "12345"

        messages = [{"role": "user", "content": "test"}]
        provider.call(model_name="echo", messages=messages)

        mock_run.assert_called_once()
        run_env = mock_run.call_args[1].get("env", {})

        # System var should be stripped
        assert "SYSTEM_SECRET_API_KEY" not in run_env
        # Explicit var should be kept
        assert run_env.get("API_KEY") == "allowed_explicit_key"

        # Cleanup
        os.environ.pop("SYSTEM_SECRET_API_KEY", None)
