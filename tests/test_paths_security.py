import os
import pytest
from pathlib import Path
from lemming.paths import validate_agent_name, get_agent_dir

class TestPathsSecurity:
    """Tests for path traversal security vulnerability fix."""

    def test_validate_agent_name_valid(self):
        """Test valid agent names."""
        validate_agent_name("valid_agent")
        validate_agent_name("agent-123")
        validate_agent_name("agent_name")

    def test_validate_agent_name_empty(self):
        """Test empty agent name raises ValueError."""
        with pytest.raises(ValueError, match="Agent name cannot be empty"):
            validate_agent_name("")

    def test_validate_agent_name_dot(self):
        """Test '.' raises ValueError."""
        with pytest.raises(ValueError, match="is invalid"):
            validate_agent_name(".")

    def test_validate_agent_name_dotdot(self):
        """Test '..' raises ValueError."""
        with pytest.raises(ValueError, match="is invalid"):
            validate_agent_name("..")

    def test_validate_agent_name_slash(self):
        """Test names with forward slash raise ValueError."""
        with pytest.raises(ValueError, match="contains path separators"):
            validate_agent_name("path/traversal")

    def test_validate_agent_name_absolute(self):
        """Test absolute paths raise ValueError."""
        with pytest.raises(ValueError, match="contains path separators"):
            validate_agent_name("/etc/passwd")

    def test_get_agent_dir_security(self, tmp_path):
        """Test get_agent_dir enforces validation."""
        base_path = tmp_path

        # Should work for valid name
        assert get_agent_dir(base_path, "good_agent") == base_path / "agents" / "good_agent"

        # Should fail for traversal attempts
        with pytest.raises(ValueError):
            get_agent_dir(base_path, "../bad_agent")

        with pytest.raises(ValueError):
            get_agent_dir(base_path, "/tmp/bad_agent")
