"""Tests for memory system - simplified to match actual API."""

from __future__ import annotations

import json
from pathlib import Path

from lemming.memory import get_memory_context, load_memory, save_memory


def test_save_and_load_memory(tmp_path: Path) -> None:
    """Test saving and loading memory."""
    agent_dir = tmp_path / "agents" / "test_agent"
    agent_dir.mkdir(parents=True)

    save_memory(tmp_path, "test_agent", "test_key", {"data": "value"})

    loaded = load_memory(tmp_path, "test_agent", "test_key")
    assert loaded == {"data": "value"}


def test_load_memory_missing(tmp_path: Path) -> None:
    """Test loading memory when it doesn't exist."""
    agent_dir = tmp_path / "agents" / "test_agent"
    agent_dir.mkdir(parents=True)

    loaded = load_memory(tmp_path, "test_agent", "missing_key")
    assert loaded is None


def test_save_memory_creates_directory(tmp_path: Path) -> None:
    """Test that save_memory creates the memory directory."""
    save_memory(tmp_path, "new_agent", "key1", "value1")

    memory_dir = tmp_path / "agents" / "new_agent" / "memory"
    assert memory_dir.exists()
    assert (memory_dir / "key1.json").exists()


def test_get_memory_context_empty(tmp_path: Path) -> None:
    """Test getting memory context when empty."""
    agent_dir = tmp_path / "agents" / "test_agent"
    agent_dir.mkdir(parents=True)

    context = get_memory_context(tmp_path, "test_agent")
    assert "no memory" in context.lower() or "empty" in context.lower()


def test_get_memory_context_with_data(tmp_path: Path) -> None:
    """Test getting memory context with data."""
    agent_dir = tmp_path / "agents" / "test_agent"
    agent_dir.mkdir(parents=True)

    save_memory(tmp_path, "test_agent", "notes", "important note")
    save_memory(tmp_path, "test_agent", "preferences", ["item1", "item2"])

    context = get_memory_context(tmp_path, "test_agent")
    # Context should include the saved keys
    assert "notes" in context or "preferences" in context


def test_memory_with_complex_types(tmp_path: Path) -> None:
    """Test memory with complex nested data structures."""
    agent_dir = tmp_path / "agents" / "test_agent"
    agent_dir.mkdir(parents=True)

    complex_data = {
        "nested": {
            "level1": {
                "level2": ["a", "b", "c"],
            }
        },
        "list_of_dicts": [
            {"id": 1, "value": "first"},
            {"id": 2, "value": "second"},
        ],
    }
    save_memory(tmp_path, "test_agent", "complex", complex_data)

    loaded = load_memory(tmp_path, "test_agent", "complex")
    assert loaded == complex_data
    assert loaded["nested"]["level1"]["level2"] == ["a", "b", "c"]


def test_memory_overwrites(tmp_path: Path) -> None:
    """Test that saving to the same key overwrites."""
    agent_dir = tmp_path / "agents" / "test_agent"
    agent_dir.mkdir(parents=True)

    save_memory(tmp_path, "test_agent", "key1", "value1")
    save_memory(tmp_path, "test_agent", "key1", "value2")

    loaded = load_memory(tmp_path, "test_agent", "key1")
    assert loaded == "value2"
