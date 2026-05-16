import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from lemming import api


@pytest.fixture
def client():
    return TestClient(api.app)


def test_websocket_auth_not_configured(client):
    """Verify websocket is accessible when no admin key is set."""
    # Ensure LEMMING_ADMIN_KEY is not set
    with patch.dict(os.environ, {}, clear=False):
        if "LEMMING_ADMIN_KEY" in os.environ:
            del os.environ["LEMMING_ADMIN_KEY"]

        with client.websocket_connect("/ws") as websocket:
            data = websocket.receive_json()
            assert "status" in data


def test_websocket_auth_failure(client):
    """Verify websocket is rejected when admin key is set and no key provided."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret"}):
        # TestClient raises on connection rejection
        with pytest.raises(Exception):
            with client.websocket_connect("/ws"):
                pass


def test_websocket_auth_success_query(client):
    """Verify websocket is accepted with correct query key."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret"}):
        with client.websocket_connect("/ws?key=secret") as websocket:
            data = websocket.receive_json()
            assert "status" in data


def test_websocket_auth_success_header(client):
    """Verify websocket is accepted with correct header key."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret"}):
        with client.websocket_connect("/ws", headers={"X-Admin-Key": "secret"}) as websocket:
            data = websocket.receive_json()
            assert "status" in data
