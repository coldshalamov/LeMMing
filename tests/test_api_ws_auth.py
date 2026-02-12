import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from lemming import api


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


def test_websocket_should_reject_no_auth(client: TestClient):
    """Verify WebSocket rejects connection when admin key is set but not provided."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}):
        # We expect connection failure (handshake rejected)
        with pytest.raises(Exception):
            with client.websocket_connect("/ws"):
                pass


def test_websocket_should_accept_auth_header(client: TestClient):
    """Verify WebSocket accepts connection with correct key in header."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}):
        headers = {"X-Admin-Key": "secret123"}
        with client.websocket_connect("/ws", headers=headers) as websocket:
            data = websocket.receive_json()
            assert "status" in data


def test_websocket_should_accept_auth_query(client: TestClient):
    """Verify WebSocket accepts connection with correct key in query param."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}):
        with client.websocket_connect("/ws?key=secret123") as websocket:
            data = websocket.receive_json()
            assert "status" in data
