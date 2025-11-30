"""Tests for messaging module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lemming.messaging import (
    collect_incoming_messages,
    create_message,
    mark_message_processed,
    send_message,
)


def test_create_message():
    """Test message creation."""
    msg = create_message(
        sender="manager",
        receiver="planner",
        content="Test content",
        importance="high",
        ttl_turns=10,
        current_turn=5,
    )

    assert msg.sender == "manager"
    assert msg.receiver == "planner"
    assert msg.content == "Test content"
    assert msg.importance == "high"
    assert msg.ttl_turns == 10
    assert msg.turn_created == 5
    assert msg.id is not None
    assert msg.timestamp is not None


def test_create_message_defaults():
    """Test message creation with defaults."""
    msg = create_message(sender="manager", receiver="planner", content="Test")

    assert msg.importance == "normal"
    assert msg.ttl_turns == 24
    assert msg.turn_created == 0
    assert msg.instructions is None


def test_send_message(temp_base_path: Path, setup_config_files, mock_org_chart):
    """Test sending a message."""
    msg = create_message("manager", "planner", "Hello planner")
    send_message(temp_base_path, msg)

    msg_path = temp_base_path / "agents" / "manager" / "outbox" / "planner" / f"msg_{msg.id}.json"
    assert msg_path.exists()

    with msg_path.open("r") as f:
        saved = json.load(f)

    assert saved["sender"] == "manager"
    assert saved["receiver"] == "planner"
    assert saved["content"] == "Hello planner"


def test_send_message_permission_error(temp_base_path: Path, setup_config_files):
    """Test sending message without permission."""
    msg = create_message("planner", "hr", "This should fail")

    with pytest.raises(PermissionError, match="cannot send to"):
        send_message(temp_base_path, msg)


def test_collect_incoming_messages_empty(temp_base_path: Path, setup_config_files, setup_agent_dirs):
    """Test collecting messages when there are none."""
    messages = collect_incoming_messages(temp_base_path, "planner", current_turn=1)
    assert len(messages) == 0


def test_collect_incoming_messages(temp_base_path: Path, setup_config_files, setup_agent_dirs):
    """Test collecting incoming messages."""
    # Send messages from manager to planner
    msg1 = create_message("manager", "planner", "Message 1", current_turn=1)
    msg2 = create_message("manager", "planner", "Message 2", current_turn=2)
    send_message(temp_base_path, msg1)
    send_message(temp_base_path, msg2)

    messages = collect_incoming_messages(temp_base_path, "planner", current_turn=5)
    assert len(messages) == 2
    assert messages[0].content in ["Message 1", "Message 2"]
    assert messages[1].content in ["Message 1", "Message 2"]


def test_collect_incoming_messages_expired(temp_base_path: Path, setup_config_files, setup_agent_dirs):
    """Test that expired messages are not collected."""
    # Message with TTL that expires
    msg = create_message("manager", "planner", "Old message", ttl_turns=5, current_turn=1)
    send_message(temp_base_path, msg)

    # Current turn is beyond TTL
    messages = collect_incoming_messages(temp_base_path, "planner", current_turn=10)
    assert len(messages) == 0


def test_collect_incoming_messages_no_ttl(temp_base_path: Path, setup_config_files, setup_agent_dirs):
    """Test messages with no TTL are always collected."""
    msg = create_message("manager", "planner", "Permanent message", ttl_turns=None, current_turn=1)
    send_message(temp_base_path, msg)

    messages = collect_incoming_messages(temp_base_path, "planner", current_turn=1000)
    assert len(messages) == 1


def test_mark_message_processed(temp_base_path: Path, setup_config_files, setup_agent_dirs):
    """Test marking a message as processed."""
    msg = create_message("manager", "planner", "Test message")
    send_message(temp_base_path, msg)

    msg_path = temp_base_path / "agents" / "manager" / "outbox" / "planner" / f"msg_{msg.id}.json"
    assert msg_path.exists()

    mark_message_processed(temp_base_path, msg)

    # Original should be gone
    assert not msg_path.exists()

    # Should be in processed
    processed_path = msg_path.parent / "processed" / msg_path.name
    assert processed_path.exists()


def test_mark_message_processed_nonexistent(temp_base_path: Path, setup_config_files):
    """Test marking a nonexistent message as processed (should not error)."""
    msg = create_message("manager", "planner", "Nonexistent")
    mark_message_processed(temp_base_path, msg)  # Should not raise


def test_collect_from_multiple_senders(temp_base_path: Path, setup_config_files, setup_agent_dirs):
    """Test collecting messages from multiple senders."""
    msg1 = create_message("planner", "manager", "From planner", current_turn=1)
    msg2 = create_message("hr", "manager", "From HR", current_turn=1)
    send_message(temp_base_path, msg1)
    send_message(temp_base_path, msg2)

    messages = collect_incoming_messages(temp_base_path, "manager", current_turn=5)
    assert len(messages) == 2
    contents = {m.content for m in messages}
    assert "From planner" in contents
    assert "From HR" in contents
