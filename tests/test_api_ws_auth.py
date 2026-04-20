import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# We need to import app after setting environment variable or patch it.
# Since app is already imported in test modules usually, we rely on patching os.environ in the test.
from lemming.api import app


def test_websocket_auth_missing_key():
    """Test that WS connection fails when admin key is set but not provided."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "super-secret-key"}):
        client = TestClient(app)
        with pytest.raises(Exception):  # starlette/fastapi test client raises WebSocketDisconnect or similar on 403
            with client.websocket_connect("/ws"):
                pass


def test_websocket_auth_valid_key_header():
    """Test that WS connection succeeds with valid key in header."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "super-secret-key"}):
        client = TestClient(app)
        headers = {"X-Admin-Key": "super-secret-key"}
        with client.websocket_connect("/ws", headers=headers) as websocket:
            data = websocket.receive_json()
            assert "status" in data
            assert "messages" in data


def test_websocket_auth_valid_key_query_param():
    """Test that WS connection succeeds with valid key in query param."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "super-secret-key"}):
        client = TestClient(app)
        with client.websocket_connect("/ws?key=super-secret-key") as websocket:
            data = websocket.receive_json()
            assert "status" in data
            assert "messages" in data


def test_websocket_no_admin_key_configured():
    """Test that WS connection succeeds when no admin key is configured."""
    with patch.dict(os.environ, {}, clear=True):
        client = TestClient(app)
        with client.websocket_connect("/ws") as websocket:
            data = websocket.receive_json()
            assert "status" in data
