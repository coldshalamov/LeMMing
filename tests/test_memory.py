from pathlib import Path

import pytest

from lemming import memory


def test_append_and_load_recent_events(tmp_path: Path):
    agent = "tester"
    base_path = tmp_path
    memory.append_memory_event(base_path, agent, "preferences", "first", max_entries=2)
    memory.append_memory_event(base_path, agent, "preferences", "second", max_entries=2)
    memory.append_memory_event(base_path, agent, "preferences", "third", max_entries=2)

    recent = memory.load_recent_memory_events(base_path, agent, "preferences", limit=5)
    assert len(recent) == 2
    assert recent[-1]["event"] == "third"


def test_summarize_memory_events_handles_empty(tmp_path: Path):
    summary = memory.summarize_memory_events(tmp_path, "agent", "missing")
    assert "No recorded events" in summary


def test_append_memory_event_rejects_non_list(tmp_path: Path):
    agent = "tester"
    bad_file = tmp_path / "agents" / agent / "memory"
    bad_file.mkdir(parents=True, exist_ok=True)
    (bad_file / "preferences.json").write_text('{"value": "not-a-list"}')

    with pytest.raises(ValueError):
        memory.append_memory_event(tmp_path, agent, "preferences", "oops")
