import pytest
from pathlib import Path
from lemming.memory import (
    save_memory, load_memory, delete_memory, list_memories, archive_old_memories
)

class TestMemoryPerfBehavior:
    @pytest.fixture
    def test_env(self, tmp_path):
        base_path = tmp_path / "lemming"
        base_path.mkdir()
        agent_name = "perf_agent"
        return base_path, agent_name

    def test_save_creates_directory(self, test_env):
        base_path, agent_name = test_env
        key = "test_key"
        value = {"foo": "bar"}
        save_memory(base_path, agent_name, key, value)
        loaded = load_memory(base_path, agent_name, key)
        assert loaded == value

    def test_load_missing_returns_none(self, test_env):
        base_path, agent_name = test_env
        result = load_memory(base_path, agent_name, "non_existent")
        assert result is None

    def test_delete_missing_returns_false(self, test_env):
        base_path, agent_name = test_env
        result = delete_memory(base_path, agent_name, "non_existent")
        assert result is False

    def test_full_cycle(self, test_env):
        base_path, agent_name = test_env
        key = "cycle"
        value = [1, 2, 3]
        save_memory(base_path, agent_name, key, value)
        assert load_memory(base_path, agent_name, key) == value
        assert key in list_memories(base_path, agent_name)
        assert delete_memory(base_path, agent_name, key) is True
        assert load_memory(base_path, agent_name, key) is None
        assert delete_memory(base_path, agent_name, key) is False

    def test_list_memories_missing_dir(self, test_env):
        base_path, agent_name = test_env
        # Agent dir does not exist
        result = list_memories(base_path, "ghost_agent")
        assert result == []

    def test_archive_missing_dir(self, test_env):
        base_path, agent_name = test_env
        # Agent dir does not exist, should return 0 and NOT crash
        result = archive_old_memories(base_path, "ghost_agent")
        assert result == 0
