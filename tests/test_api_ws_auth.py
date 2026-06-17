import os
from unittest.mock import patch

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from lemming import api


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


def test_ws_auth_required_fail(client: TestClient):
    """Verify WebSocket connection is rejected when admin key is set and no/wrong key is provided."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}):
        # Without header
        try:
            with client.websocket_connect("/ws") as _:
                pytest.fail("WebSocket connection should have been rejected (missing key)")
        except (WebSocketDisconnect, Exception):
            pass

        # With wrong header
        try:
            with client.websocket_connect("/ws", headers={"X-Admin-Key": "wrong"}) as _:
                pytest.fail("WebSocket connection should have been rejected (wrong key)")
        except (WebSocketDisconnect, Exception):
            pass

        # With wrong query param
        try:
            with client.websocket_connect("/ws?key=wrong") as _:
                pytest.fail("WebSocket connection should have been rejected (wrong key)")
        except (WebSocketDisconnect, Exception):
            pass


def test_ws_auth_success(client: TestClient):
    """Verify WebSocket connection is accepted when admin key is set and correct key is provided."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}):
        # 1. Via Header
        headers = {"X-Admin-Key": "secret123"}
        try:
            with client.websocket_connect("/ws", headers=headers) as websocket:
                data = websocket.receive_json()
                assert "status" in data
        except Exception as e:
            pytest.fail(f"WebSocket connection failed with correct header key: {e}")

        # 2. Via Query Param
        try:
            with client.websocket_connect("/ws?key=secret123") as websocket:
                data = websocket.receive_json()
                assert "status" in data
        except Exception as e:
            pytest.fail(f"WebSocket connection failed with correct query param key: {e}")
