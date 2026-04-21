import pytest
import os
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
    # Since fastapi raises a generic exception or starlette.websockets.WebSocketDisconnect
    # let's just check that it disconnects or fails.
    try:
        with client.websocket_connect("/ws") as websocket:
            websocket.receive_json()
    except Exception as e:
        # Either we hit WebSocketDisconnect or RuntimeError
        pass
    else:
        pytest.fail("WebSocket did not disconnect when unauthorized.")


def test_websocket_auth_configured_with_query_param(monkeypatch):
    monkeypatch.setenv("LEMMING_ADMIN_KEY", "secret123")
    client = TestClient(app)
    with client.websocket_connect("/ws?admin_key=secret123") as websocket:
        data = websocket.receive_json()
        assert "status" in data
