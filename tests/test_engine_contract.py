from __future__ import annotations

import logging

from lemming.engine import _parse_llm_output


def test_parse_valid_json():
    raw = (
        '{"outbox_entries": [{"kind": "message", "payload": {"text": "hi"}, "tags": ["info"]}],'
        ' "tool_calls": [{"tool": "ping"}],'
        ' "memory_updates": [{"key": "foo", "value": {"bar": 1}}],'
        ' "notes": "ok"}'
    )
    parsed = _parse_llm_output(raw, agent_name="agent1", tick=5)
    assert parsed["notes"] == "ok"
    assert parsed["outbox_entries"][0]["payload"]["text"] == "hi"
    assert parsed["tool_calls"] == [{"tool": "ping"}]
    assert parsed["memory_updates"] == [{"key": "foo", "value": {"bar": 1}, "op": None}]


def test_parse_with_fences():
    raw = """```json\n{\n  \"notes\": \"No action needed.\"\n}\n```"""
    parsed = _parse_llm_output(raw, agent_name="agent1", tick=1)
    assert parsed == {
        "outbox_entries": [],
        "tool_calls": [],
        "memory_updates": [],
        "notes": "No action needed.",
    }


def test_missing_keys_warns(caplog):
    caplog.set_level(logging.WARNING)
    parsed = _parse_llm_output("{\"notes\":\"only\"}", agent_name="agent1", tick=6)
    assert parsed["notes"] == "only"
    assert parsed["outbox_entries"] == []
    assert any("missing keys" in message for message in caplog.messages)


def test_invalid_json_contract_violation(caplog):
    caplog.set_level(logging.WARNING)
    parsed = _parse_llm_output("not-json", agent_name="agent1", tick=2)
    assert parsed == {
        "outbox_entries": [],
        "tool_calls": [],
        "memory_updates": [],
        "notes": "",
    }
    assert any("not valid JSON" in msg for msg in caplog.messages)


def test_non_object_contract_violation(caplog):
    caplog.set_level(logging.WARNING)
    parsed = _parse_llm_output("[]", agent_name="agent1", tick=3)
    assert parsed["outbox_entries"] == []
    assert any("expected a JSON object" in msg for msg in caplog.messages)


def test_rejects_bad_fields(caplog):
    caplog.set_level(logging.WARNING)
    raw = (
        '{"outbox_entries": ["bad", {"payload": "oops"}],'
        ' "memory_updates": [{"value": 1}, "oops"],'
        ' "tool_calls": "wrong", "notes": 5}'
    )
    parsed = _parse_llm_output(raw, agent_name="agent1", tick=4)
    # Only the dict outbox entry should survive and be sanitized
    assert parsed["outbox_entries"] == [
        {"kind": "message", "payload": {}, "tags": [], "meta": {}, "recipients": None}
    ]
    # Invalid memory updates are dropped
    assert parsed["memory_updates"] == []
    # tool_calls coerced to empty list on violation
    assert parsed["tool_calls"] == []
    assert parsed["notes"] == "5"
    assert any("must be a list" in msg for msg in caplog.messages)
    assert any("memory update" in msg for msg in caplog.messages)
