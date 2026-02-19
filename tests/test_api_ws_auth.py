import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from lemming import api


@pytest.fixture
def client() -> TestClient:
    api._request_timestamps.clear()
    return TestClient(api.app)


def test_ws_auth_not_configured(client: TestClient, tmp_path):
    """Verify WebSocket is accessible when no admin key is set."""
    with (
        patch.dict(os.environ, {}, clear=False),
        patch("lemming.api.BASE_PATH", tmp_path),
        patch("lemming.api.SECRETS_PATH", tmp_path / "secrets.json"),
    ):
        if "LEMMING_ADMIN_KEY" in os.environ:
            del os.environ["LEMMING_ADMIN_KEY"]

        # Setup minimal environment
        config_dir = tmp_path / "lemming" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "tick.json").write_text("0")
        (config_dir / "org_config.json").write_text('{"base_turn_seconds": 1}')
        (config_dir / "credits.json").write_text("{}")
        (config_dir / "models.json").write_text("{}")
        if not (tmp_path / "agents").exists():
            (tmp_path / "agents").mkdir()

        # Should connect successfully
        with client.websocket_connect("/ws") as websocket:
            data = websocket.receive_json()
            assert "status" in data


def test_ws_auth_configured_success_query_param(client: TestClient, tmp_path):
    """Verify WebSocket access is allowed with correct key in query param."""
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

        with client.websocket_connect("/ws?key=secret123") as websocket:
            data = websocket.receive_json()
            assert "status" in data


def test_ws_auth_configured_success_header(client: TestClient, tmp_path):
    """Verify WebSocket access is allowed with correct key in header."""
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

        # TestClient.websocket_connect accepts headers
        with client.websocket_connect("/ws", headers={"X-Admin-Key": "secret123"}) as websocket:
            data = websocket.receive_json()
            assert "status" in data


def test_ws_auth_configured_failure(client: TestClient, tmp_path):
    """Verify WebSocket access is denied without correct key."""
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

        # No key
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/ws") as websocket:
                pass
        # 1008 is Policy Violation
        assert exc.value.code == 1008

        # Wrong key
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/ws?key=wrong") as websocket:
                pass
        assert exc.value.code == 1008
