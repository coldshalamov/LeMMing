import shutil
from pathlib import Path
import pytest
from lemming.tools import MemoryWriteTool, MemoryReadTool, ToolResult
from lemming.memory import validate_memory_key

class TestMemorySecurity:
    @pytest.fixture
    def test_env(self, tmp_path):
        base_path = tmp_path / "lemming"
        base_path.mkdir()
        agent_name = "victim_agent"
        agent_dir = base_path / "agents" / agent_name
        agent_dir.mkdir(parents=True)
        memory_dir = agent_dir / "memory"
        memory_dir.mkdir(parents=True)
        return base_path, agent_name, agent_dir

    def test_memory_write_traversal_blocked(self, test_env):
        base_path, agent_name, agent_dir = test_env
        tool = MemoryWriteTool()

        # Attempt to write outside memory directory using ".."
        evil_key = "../pwned"
        result = tool.execute(agent_name, base_path, key=evil_key, value="malicious")

        assert not result.success
        assert "Invalid memory key" in result.error

        # Verify file does not exist
        assert not (agent_dir / "pwned.json").exists()

    def test_memory_read_traversal_blocked(self, test_env):
        base_path, agent_name, agent_dir = test_env

        # Create a secret file outside memory
        secret_file = agent_dir / "secret.json"
        secret_file.write_text('{"value": "SECRET"}')

        tool = MemoryReadTool()
        evil_key = "../secret"

        result = tool.execute(agent_name, base_path, key=evil_key)

        assert not result.success
        assert result.output == "" # Memory not found or invalid key returns None -> Memory not found

    def test_memory_key_validation(self):
        # Valid keys
        validate_memory_key("valid_key")
        validate_memory_key("valid-key")
        validate_memory_key("valid_key_123")

        # Invalid keys
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_memory_key("")

        with pytest.raises(ValueError, match="invalid"):
            validate_memory_key("invalid/key")

        with pytest.raises(ValueError, match="invalid"):
            validate_memory_key("..")

        with pytest.raises(ValueError, match="invalid"):
            validate_memory_key("key with spaces")
