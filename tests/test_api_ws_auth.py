import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from lemming.api import app


def test_websocket_auth_not_configured():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        assert "status" in data


def test_websocket_auth_configured_no_header(monkeypatch):
    monkeypatch.setenv("LEMMING_ADMIN_KEY", "secret123")
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws") as websocket:
            websocket.receive_json()
    assert exc.value.code == 1008


def test_websocket_auth_configured_with_query_param(monkeypatch):
    monkeypatch.setenv("LEMMING_ADMIN_KEY", "secret123")
    client = TestClient(app)
    with client.websocket_connect("/ws?admin_key=secret123") as websocket:
        data = websocket.receive_json()
        assert "status" in data
