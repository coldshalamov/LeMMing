import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from lemming import api


@pytest.fixture
def client() -> TestClient:
    api._request_timestamps.clear()
    return TestClient(api.app)


def test_websocket_auth_not_configured(client: TestClient, tmp_path):
    """Verify WebSocket is accessible when no admin key is set."""
    with patch.dict(os.environ, {}, clear=False):
        if "LEMMING_ADMIN_KEY" in os.environ:
            del os.environ["LEMMING_ADMIN_KEY"]

        with patch("lemming.api.BASE_PATH", tmp_path), patch("lemming.api.SECRETS_PATH", tmp_path / "secrets.json"):

            # Setup minimal environment
            config_dir = tmp_path / "lemming" / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "tick.json").write_text("0")
            (config_dir / "org_config.json").write_text('{"base_turn_seconds": 1}')
            (config_dir / "credits.json").write_text("{}")
            (config_dir / "models.json").write_text("{}")
            if not (tmp_path / "agents").exists():
                (tmp_path / "agents").mkdir()

            with client.websocket_connect("/ws") as websocket:
                data = websocket.receive_json()
                assert "status" in data
                assert "messages" in data


def test_websocket_auth_configured_success(client: TestClient, tmp_path):
    """Verify WebSocket access is allowed with correct key when configured."""
    with (
        patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}),
        patch("lemming.api.BASE_PATH", tmp_path),
        patch("lemming.api.SECRETS_PATH", tmp_path / "secrets.json"),
    ):

        # Setup minimal environment
        config_dir = tmp_path / "lemming" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "tick.json").write_text("0")
        (config_dir / "org_config.json").write_text('{"base_turn_seconds": 1}')
        (config_dir / "credits.json").write_text("{}")
        (config_dir / "models.json").write_text("{}")
        if not (tmp_path / "agents").exists():
            (tmp_path / "agents").mkdir()

        # Test with query parameter
        with client.websocket_connect("/ws?key=secret123") as websocket:
            data = websocket.receive_json()
            assert "status" in data

        # Test with header
        with client.websocket_connect("/ws", headers={"X-Admin-Key": "secret123"}) as websocket:
            data = websocket.receive_json()
            assert "status" in data


def test_websocket_auth_configured_failure(client: TestClient, tmp_path):
    """Verify WebSocket access is denied without correct key when configured."""
    with (
        patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}),
        patch("lemming.api.BASE_PATH", tmp_path),
        patch("lemming.api.SECRETS_PATH", tmp_path / "secrets.json"),
    ):

        # Setup minimal environment
        config_dir = tmp_path / "lemming" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "tick.json").write_text("0")
        (config_dir / "org_config.json").write_text('{"base_turn_seconds": 1}')
        (config_dir / "credits.json").write_text("{}")
        (config_dir / "models.json").write_text("{}")
        if not (tmp_path / "agents").exists():
            (tmp_path / "agents").mkdir()

        # No auth
        # Depending on client impl, could be WebSocketDisconnect or HTTP 403
        with pytest.raises(Exception):
            with client.websocket_connect("/ws"):
                pass
