from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from lemming import api
from lemming.engine import persist_tick
from lemming.messages import OutboxEntry, write_outbox_entry


def _setup_base(tmp_path: Path) -> Path:
    config_dir = tmp_path / "lemming" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "org_config.json").write_text(
        json.dumps({"base_turn_seconds": 1, "max_turns": None}), encoding="utf-8"
    )
    (config_dir / "credits.json").write_text(
        json.dumps({"alice": {"model": "demo", "credits_left": 10.0, "max_credits": 20.0, "soft_cap": 20.0}}),
        encoding="utf-8",
    )

    agent_dir = tmp_path / "agents" / "alice"
    agent_dir.mkdir(parents=True)
    resume = {
        "name": "alice",
        "title": "Demo agent",
        "short_description": "Testing agent",
        "model": {"key": "demo-model"},
        "permissions": {"read_outboxes": [], "tools": []},
        "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},
        "instructions": "",
    }
    (agent_dir / "resume.json").write_text(json.dumps(resume), encoding="utf-8")

    entry = OutboxEntry.create(agent="alice", tick=2, kind="message", payload={"text": "hello"})
    write_outbox_entry(tmp_path, "alice", entry)

    return tmp_path


def _client_for_base(base_path: Path) -> TestClient:
    api.BASE_PATH = base_path
    return TestClient(api.app)


def test_api_agents_returns_all_valid_agents(tmp_path: Path) -> None:
    base = _setup_base(tmp_path)
    client = _client_for_base(base)

    response = client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "alice"
    assert data[0]["schedule"]["run_every_n_ticks"] == 1
    assert data[0]["credits"]["credits_left"] == 10.0


def test_api_status_reports_tick_and_counts(tmp_path: Path) -> None:
    base = _setup_base(tmp_path)
    persist_tick(base, 5)
    client = _client_for_base(base)

    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()

    assert data["tick"] == 5
    assert data["total_agents"] == 1
    assert data["total_messages"] == 1
    assert data["total_credits"] == 10.0


def test_api_messages_returns_recent_outbox_entries(tmp_path: Path) -> None:
    base = _setup_base(tmp_path)
    later_entry = OutboxEntry.create(agent="alice", tick=3, kind="report", payload={"text": "later"})
    write_outbox_entry(base, "alice", later_entry)
    client = _client_for_base(base)

    response = client.get("/api/messages?limit=5")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["tick"] >= data[1]["tick"]
    assert {entry["kind"] for entry in data} == {"message", "report"}
