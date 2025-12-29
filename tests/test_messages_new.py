from pathlib import Path

from lemming.messages import (
    OutboxEntry,
    collect_readable_outboxes,
    outbox_filename,
    read_outbox_entries,
    write_outbox_entry,
)


def test_create_entry() -> None:
    entry = OutboxEntry.create(
        agent="tester",
        tick=5,
        kind="message",
        payload={"text": "hello"},
    )
    assert entry.agent == "tester"
    assert entry.tick == 5
    assert entry.id
    assert entry.created_at


def test_write_and_read(tmp_path: Path) -> None:
    entry = OutboxEntry.create(agent="sender", tick=1, kind="message", payload={"text": "hi"})
    saved = write_outbox_entry(tmp_path, "sender", entry)
    assert saved.name == outbox_filename(entry)

    entries = read_outbox_entries(tmp_path, "sender")
    assert len(entries) == 1
    assert entries[0].payload["text"] == "hi"
    assert entries[0].created_at == entry.created_at


def test_collect_with_wildcard(tmp_path: Path) -> None:
    for name in ["agent_a", "agent_b"]:
        agent_dir = tmp_path / "agents" / name
        agent_dir.mkdir(parents=True)
        entry = OutboxEntry.create(agent=name, tick=1, kind="msg", payload={"text": name})
        write_outbox_entry(tmp_path, name, entry)

    entries = collect_readable_outboxes(tmp_path, "reader", ["*"])
    assert len(entries) == 2


def test_outbox_entry_roundtrip_and_timestamp_alias() -> None:
    entry = OutboxEntry.create(agent="alice", tick=7, kind="report", payload={"value": 1}, tags=["note"])

    as_dict = entry.to_dict()
    restored = OutboxEntry.from_dict(as_dict)

    assert restored == entry

    legacy_dict = dict(as_dict)
    legacy_dict.pop("created_at")
    legacy_dict["timestamp"] = entry.created_at

    restored_from_legacy = OutboxEntry.from_dict(legacy_dict)

    assert restored_from_legacy.created_at == entry.created_at
    assert restored_from_legacy.agent == entry.agent
