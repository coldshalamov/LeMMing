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
    """Verify that CLIProvider sanitizes sensitive environment variables."""
    import os

    with patch.dict(os.environ, {"SECRET_KEY": "should_be_removed", "NORMAL_VAR": "should_stay"}):
        provider = CLIProvider(command=["echo"])
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="mock output", stderr="", returncode=0)
            provider.call(model_name="echo", messages=[{"role": "user", "content": "hello"}])

            mock_run.assert_called_once()
            called_env = mock_run.call_args[1].get("env", {})
            assert "SECRET_KEY" not in called_env
            assert "NORMAL_VAR" in called_env


def test_cli_provider_env_override():
    """Verify that explicitly provided env vars are preserved."""
    import os

    with patch.dict(os.environ, {"SECRET_KEY": "should_be_removed"}):
        provider = CLIProvider(command=["echo"], env={"SECRET_KEY": "explicitly_provided"})
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="mock output", stderr="", returncode=0)
            provider.call(model_name="echo", messages=[{"role": "user", "content": "hello"}])

            mock_run.assert_called_once()
            called_env = mock_run.call_args[1].get("env", {})
            assert called_env.get("SECRET_KEY") == "explicitly_provided"
