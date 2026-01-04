
import json
import os
import shutil
import tempfile
import pytest
from pathlib import Path
from lemming.messages import read_outbox_entries, OutboxEntry, write_outbox_entry
from lemming.paths import get_outbox_dir

@pytest.fixture
def temp_home():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)

def test_read_outbox_ignores_garbage_files(temp_home):
    agent_name = "test_agent"

    # Create valid entries
    for i in range(10):
        entry = OutboxEntry.create(agent_name, tick=100+i, kind="test", payload={"i": i})
        write_outbox_entry(temp_home, agent_name, entry)

    # Create garbage files that sort "higher" than valid entries (strings)
    # "z_garbage.json" > "00000109_...json"
    outbox_dir = get_outbox_dir(temp_home, agent_name)
    # Ensure dir exists (write_outbox_entry creates it, but just in case)
    outbox_dir.mkdir(parents=True, exist_ok=True)

    # Create enough garbage to fill the 'limit' if logic is broken
    for i in range(60):
        with (outbox_dir / f"z_garbage_{i}.json").open("w") as f:
            json.dump({"garbage": True}, f)

    # Also create files that start with letters but look like json
    with (outbox_dir / "resume.json").open("w") as f:
        json.dump({"name": "resume"}, f)

    # Read entries with limit=5
    entries = read_outbox_entries(temp_home, agent_name, limit=5)

    assert len(entries) == 5
    # Should be the newest valid entries (ticks 109, 108, 107, 106, 105)
    ticks = [e.tick for e in entries]
    assert ticks == [109, 108, 107, 106, 105]

def test_read_outbox_performance_optimization(temp_home):
    # This test primarily verifies correctness of the optimized logic
    agent_name = "perf_agent"

    # Create entries with gaps
    ticks = [10, 20, 30, 40, 50]
    for t in ticks:
        entry = OutboxEntry.create(agent_name, tick=t, kind="test", payload={"t": t})
        write_outbox_entry(temp_home, agent_name, entry)

    entries = read_outbox_entries(temp_home, agent_name, limit=3)
    assert len(entries) == 3
    assert [e.tick for e in entries] == [50, 40, 30]
