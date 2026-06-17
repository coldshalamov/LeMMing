from unittest.mock import MagicMock, patch

import pytest

from lemming.providers import CLIProvider


def test_cli_provider_arg_injection_bypass_whitespace():
    """Verify that CLIProvider catches flags even if preceded by whitespace."""
    provider = CLIProvider(command=["echo"])

    # Mock subprocess.run
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="mock output", stderr="", returncode=0)

        # Simulate a prompt that bypasses startswith("-") via whitespace
        prompt = " -injected_flag"
        messages = [{"role": "user", "content": prompt}]

        # Expect Security Violation
        with pytest.raises(ValueError, match="Security violation"):
            provider.call(model_name="echo", messages=messages)

        # Ensure subprocess was NOT called
        mock_run.assert_not_called()
