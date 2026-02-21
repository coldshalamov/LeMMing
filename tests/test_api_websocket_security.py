
import os
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from lemming.api import app, _request_timestamps

@pytest.fixture
def client():
    _request_timestamps.clear()
    return TestClient(app)

def test_websocket_auth_enforced(client, monkeypatch):
    """
    Test that the WebSocket endpoint denies access without key when LEMMING_ADMIN_KEY is set.
    """
    monkeypatch.setenv("LEMMING_ADMIN_KEY", "secret123")

    # Expect connection failure (403 or 1008)
    # TestClient raises WebSocketDisconnect on closure
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws") as websocket:
            websocket.receive_json()

    # 1008 is Policy Violation
    assert exc.value.code == 1008

def test_websocket_auth_allowed_with_query_param(client, monkeypatch):
    """
    Test that the WebSocket endpoint allows access with correct key in query param.
    """
    monkeypatch.setenv("LEMMING_ADMIN_KEY", "secret123")

    with client.websocket_connect("/ws?key=secret123") as websocket:
        data = websocket.receive_json()
        assert "status" in data

def test_websocket_auth_allowed_with_header(client, monkeypatch):
    """
    Test that the WebSocket endpoint allows access with correct key in header.
    """
    monkeypatch.setenv("LEMMING_ADMIN_KEY", "secret123")

    with client.websocket_connect("/ws", headers={"X-Admin-Key": "secret123"}) as websocket:
        data = websocket.receive_json()
        assert "status" in data

def test_send_message_auth_enforced(client, monkeypatch):
    """
    Test that sending messages denies access without key when LEMMING_ADMIN_KEY is set.
    """
    monkeypatch.setenv("LEMMING_ADMIN_KEY", "secret123")

    response = client.post("/api/messages", json={
        "target": "human",
        "text": "hello",
        "importance": "normal"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing admin key"

def test_send_message_auth_allowed(client, monkeypatch):
    """
    Test that sending messages allows access with correct key.
    """
    monkeypatch.setenv("LEMMING_ADMIN_KEY", "secret123")

    response = client.post("/api/messages", json={
        "target": "human",
        "text": "hello",
        "importance": "normal"
    }, headers={"X-Admin-Key": "secret123"})

    assert response.status_code == 200
