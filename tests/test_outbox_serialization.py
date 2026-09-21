
import pytest
from dataclasses import asdict
from lemming.messages import OutboxEntry

def test_outbox_to_dict_correctness():
    """Verify that manual to_dict implementation matches asdict structure."""
    entry = OutboxEntry.create(
        agent="test-agent",
        tick=42,
        kind="test",
        payload={"foo": "bar", "baz": [1, 2, 3]},
        tags=["a", "b"],
        recipients=["other-agent"],
        meta={"x": 1}
    )

    # Calculate expected using standard asdict
    expected = asdict(entry)

    # Get actual from method
    actual = entry.to_dict()

    assert actual == expected

    # Check that modification of returned dict does not modify original object (shallow copy check)
    # We expect top-level list/dict fields to be new objects
    assert actual["payload"] is not entry.payload
    assert actual["tags"] is not entry.tags
    assert actual["recipients"] is not entry.recipients
    assert actual["meta"] is not entry.meta

    # Verify content equality again after identity check
    assert actual["payload"] == entry.payload
    assert actual["tags"] == entry.tags
    assert actual["recipients"] == entry.recipients
    assert actual["meta"] == entry.meta

def test_outbox_to_dict_defaults():
    """Verify handling of default None values."""
    entry = OutboxEntry.create(
        agent="test-agent",
        tick=42,
        kind="test",
        payload={},
        recipients=None # explicit None
    )
    # create default sets recipients=None if not provided, but create args has it?
    # OutboxEntry.create signature: recipients: list[str] | None = None

    expected = asdict(entry)
    actual = entry.to_dict()

    assert actual == expected
    assert actual["recipients"] is None
