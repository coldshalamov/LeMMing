
import os
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from unittest.mock import patch
from lemming import api

@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)

def test_websocket_access_without_auth(client: TestClient, tmp_path):
    """Verify WebSocket is rejected without auth when admin key is set."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}):
        with patch("lemming.api.BASE_PATH", tmp_path):
            # Attempt to connect without headers should fail
            with pytest.raises(WebSocketDisconnect) as exc:
                 with client.websocket_connect("/ws") as websocket:
                    pass
            # 1008 Policy Violation
            assert exc.value.code == 1008

def test_websocket_access_with_auth(client: TestClient, tmp_path):
    """Verify WebSocket is accepted with correct auth."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}):
        with patch("lemming.api.BASE_PATH", tmp_path):
            config_dir = tmp_path / "lemming" / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "tick.json").write_text("0")
            (config_dir / "org_config.json").write_text('{"base_turn_seconds": 1}')
            (config_dir / "credits.json").write_text("{}")
            (tmp_path / "agents").mkdir()

            # Connect with header
            with client.websocket_connect("/ws", headers={"X-Admin-Key": "secret123"}) as websocket:
                data = websocket.receive_json()
                assert "status" in data

            # Connect with query param
            with client.websocket_connect("/ws?key=secret123") as websocket:
                data = websocket.receive_json()
                assert "status" in data
