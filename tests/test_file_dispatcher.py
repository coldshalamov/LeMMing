"""Tests for file_dispatcher module."""

from __future__ import annotations

from lemming.file_dispatcher import cleanup_expired_messages, ensure_outbox_path
from lemming.messaging import create_message, send_message


def test_ensure_outbox_path(temp_base_path):
    """Test ensuring outbox path exists."""
    outbox_path = temp_base_path / "agents" / "test" / "outbox" / "receiver"

    assert not outbox_path.exists()

    ensure_outbox_path(outbox_path)

    assert outbox_path.exists()
    assert (outbox_path / "processed").exists()


def test_ensure_outbox_path_idempotent(temp_base_path):
    """Test that ensure_outbox_path is idempotent."""
    outbox_path = temp_base_path / "agents" / "test" / "outbox" / "receiver"

    ensure_outbox_path(outbox_path)
    ensure_outbox_path(outbox_path)  # Should not error

    assert outbox_path.exists()


def test_cleanup_expired_messages_no_expiry(temp_base_path, setup_config_files, setup_agent_dirs):
    """Test cleanup doesn't remove messages with no TTL."""
    msg = create_message("manager", "planner", "Permanent", ttl_turns=None, current_turn=1)
    send_message(temp_base_path, msg)

    cleanup_expired_messages(temp_base_path, current_turn=1000)

    # Message should still exist
    msg_path = temp_base_path / "agents" / "manager" / "outbox" / "planner" / f"msg_{msg.id}.json"
    assert msg_path.exists()


def test_cleanup_expired_messages_removes_old(temp_base_path, setup_config_files, setup_agent_dirs):
    """Test cleanup removes expired messages."""
    msg = create_message("manager", "planner", "Old message", ttl_turns=5, current_turn=1)
    send_message(temp_base_path, msg)

    # Message expires after turn 6
    cleanup_expired_messages(temp_base_path, current_turn=10)

    msg_path = temp_base_path / "agents" / "manager" / "outbox" / "planner" / f"msg_{msg.id}.json"
    assert not msg_path.exists()


def test_cleanup_expired_messages_keeps_fresh(temp_base_path, setup_config_files, setup_agent_dirs):
    """Test cleanup keeps fresh messages."""
    msg = create_message("manager", "planner", "Fresh message", ttl_turns=20, current_turn=1)
    send_message(temp_base_path, msg)

    cleanup_expired_messages(temp_base_path, current_turn=10)

    msg_path = temp_base_path / "agents" / "manager" / "outbox" / "planner" / f"msg_{msg.id}.json"
    assert msg_path.exists()


def test_cleanup_expired_messages_mixed(temp_base_path, setup_config_files, setup_agent_dirs):
    """Test cleanup with mix of expired and fresh messages."""
    old_msg = create_message("manager", "planner", "Old", ttl_turns=5, current_turn=1)
    fresh_msg = create_message("manager", "planner", "Fresh", ttl_turns=20, current_turn=1)
    permanent_msg = create_message("manager", "planner", "Permanent", ttl_turns=None, current_turn=1)

    send_message(temp_base_path, old_msg)
    send_message(temp_base_path, fresh_msg)
    send_message(temp_base_path, permanent_msg)

    cleanup_expired_messages(temp_base_path, current_turn=10)

    # Old should be gone
    old_path = temp_base_path / "agents" / "manager" / "outbox" / "planner" / f"msg_{old_msg.id}.json"
    assert not old_path.exists()

    # Fresh should remain
    fresh_path = temp_base_path / "agents" / "manager" / "outbox" / "planner" / f"msg_{fresh_msg.id}.json"
    assert fresh_path.exists()

    # Permanent should remain
    perm_path = temp_base_path / "agents" / "manager" / "outbox" / "planner" / f"msg_{permanent_msg.id}.json"
    assert perm_path.exists()


def test_cleanup_expired_messages_empty_dir(temp_base_path):
    """Test cleanup with no agents directory."""
    cleanup_expired_messages(temp_base_path, current_turn=10)  # Should not error


def test_cleanup_expired_messages_multiple_agents(temp_base_path, setup_config_files, setup_agent_dirs):
    """Test cleanup across multiple agents."""
    msg1 = create_message("manager", "planner", "Old from manager", ttl_turns=5, current_turn=1)
    msg2 = create_message("planner", "manager", "Old from planner", ttl_turns=5, current_turn=1)

    send_message(temp_base_path, msg1)
    send_message(temp_base_path, msg2)

    cleanup_expired_messages(temp_base_path, current_turn=10)

    path1 = temp_base_path / "agents" / "manager" / "outbox" / "planner" / f"msg_{msg1.id}.json"
    path2 = temp_base_path / "agents" / "planner" / "outbox" / "manager" / f"msg_{msg2.id}.json"

    assert not path1.exists()
    assert not path2.exists()
