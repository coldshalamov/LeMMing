import os
from unittest.mock import MagicMock, patch

import pytest

from lemming.providers import CLIProvider


def test_cli_provider_arg_injection():
    """Verify that CLIProvider raises ValueError when prompt starts with '-'."""
    provider = CLIProvider(command=["echo"])

    # Mock subprocess.run
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="mock output", stderr="", returncode=0)

        # Simulate a prompt that looks like a flag
        prompt = "-injected_flag"
        messages = [{"role": "user", "content": prompt}]

        # Expect Security Violation
        with pytest.raises(ValueError, match="Security violation"):
            provider.call(model_name="echo", messages=messages)

        # Ensure subprocess was NOT called
        mock_run.assert_not_called()


def test_cli_provider_allow_arg_injection_with_config():
    """Verify that CLIProvider ALLOWS flags if prevent_arg_injection is False."""
    provider = CLIProvider(command=["echo"], prevent_arg_injection=False)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="mock output", stderr="", returncode=0)

        prompt = "-allowed_flag"
        messages = [{"role": "user", "content": prompt}]

        provider.call(model_name="echo", messages=messages)

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["echo", "-allowed_flag"]


def test_cli_provider_env_sanitization():
    """Verify that CLIProvider sanitizes secrets from the environment."""
    provider = CLIProvider(command=["env"], prevent_arg_injection=False)

    with (
        patch.dict(os.environ, {"SUPER_SECRET_API_KEY": "hidden123", "SAFE_VAR": "visible"}),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(stdout="mock output", stderr="", returncode=0)

        provider.call("test", messages=[{"role": "user", "content": ""}])

        mock_run.assert_called_once()
        run_env = mock_run.call_args[1].get("env", {})
        assert "SUPER_SECRET_API_KEY" not in run_env
        assert "SAFE_VAR" in run_env


def test_cli_provider_explicit_env_allowed():
    """Verify that explicitly provided env vars in CLIProvider are NOT sanitized."""
    provider = CLIProvider(command=["env"], env={"MY_EXPLICIT_SECRET": "allowed"}, prevent_arg_injection=False)

    with patch.dict(os.environ, {"SUPER_SECRET_API_KEY": "hidden123"}), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="mock output", stderr="", returncode=0)

        provider.call("test", messages=[{"role": "user", "content": ""}])

        mock_run.assert_called_once()
        run_env = mock_run.call_args[1].get("env", {})
        assert "SUPER_SECRET_API_KEY" not in run_env
        assert "MY_EXPLICIT_SECRET" in run_env
        assert run_env["MY_EXPLICIT_SECRET"] == "allowed"
