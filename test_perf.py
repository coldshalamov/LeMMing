import os
import pytest
from lemming.messages import format_outbox_context, OutboxEntry

def test_format_outbox_context():
    entries = [
        OutboxEntry.create(agent="a1", tick=1, kind="msg", payload={"text": "hello"}),
        OutboxEntry.create(agent="a2", tick=2, kind="msg", payload={"foo": "bar"}),
    ]
    result = format_outbox_context(entries)
    print(result)
    assert "hello" in result
    assert "foo" in result
