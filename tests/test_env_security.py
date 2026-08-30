from pathlib import Path

import pytest

from lemming.providers import CLIProvider
from lemming.tools import ShellTool


def test_shell_tool_does_not_leak_secrets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify that ShellTool does not leak sensitive environment variables to the subprocess."""
    monkeypatch.setenv("API_KEY", "super-secret-key-123")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "another-secret")
    monkeypatch.setenv("NORMAL_VAR", "normal-value")

    tool = ShellTool()
    res = tool.execute("tester", tmp_path, command="jq -n env")

    assert res.success, f"Command failed: {res.error}"
    assert "super-secret-key-123" not in res.output
    assert "another-secret" not in res.output
    assert "NORMAL_VAR" in res.output  # Normal vars should be passed


def test_cli_provider_does_not_leak_secrets(monkeypatch: pytest.MonkeyPatch):
    """Verify that CLIProvider does not leak sensitive environment variables to the subprocess."""
    monkeypatch.setenv("API_KEY", "super-secret-key-123")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "another-secret")
    monkeypatch.setenv("NORMAL_VAR", "normal-value")

    provider = CLIProvider(command=["jq", "-n", "env"], prevent_arg_injection=True)
    res = provider.call("test-model", [{"role": "user", "content": ""}])

    assert "super-secret-key-123" not in res
    assert "another-secret" not in res
    assert "NORMAL_VAR" in res
