import pytest

from lemming.paths import get_agent_dir, validate_agent_name


class TestPathsSecurity:
    """Tests for path traversal security vulnerability fix."""

    def test_validate_agent_name_valid(self):
        """Test valid agent names."""
        validate_agent_name("valid_agent")
        validate_agent_name("agent-123")
        validate_agent_name("agent_name")
        validate_agent_name("AgentName")
        validate_agent_name("123")

    def test_validate_agent_name_empty(self):
        """Test empty agent name raises ValueError."""
        with pytest.raises(ValueError, match="Agent name cannot be empty"):
            validate_agent_name("")

    def test_validate_agent_name_invalid_chars(self):
        """Test names with invalid characters raise ValueError."""
        invalid_names = [
            "agent name",  # Space
            "agent.name",  # Dot
            "agent/name",  # Slash
            "agent\\name",  # Backslash
            "agent@name",  # Special char
            "<script>",  # HTML/XML
            "foo\0bar",  # Null byte
        ]
        for name in invalid_names:
            with pytest.raises(ValueError, match="Only alphanumeric characters"):
                validate_agent_name(name)

    def test_validate_agent_name_dot(self):
        """Test '.' raises ValueError."""
        with pytest.raises(ValueError, match="Only alphanumeric characters"):
            validate_agent_name(".")

    def test_validate_agent_name_dotdot(self):
        """Test '..' raises ValueError."""
        with pytest.raises(ValueError, match="Only alphanumeric characters"):
            validate_agent_name("..")

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

        # Should fail for spaces
        with pytest.raises(ValueError):
            get_agent_dir(base_path, "bad agent")
