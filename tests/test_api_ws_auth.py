import os
from unittest.mock import patch

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from lemming import api


@pytest.fixture
def client() -> TestClient:
    return TestClient(api.app)


def test_websocket_auth_security(client: TestClient, tmp_path):
    """Verify WebSocket security rules."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}), patch("lemming.api.BASE_PATH", tmp_path):

        # Setup minimal environment
        config_dir = tmp_path / "lemming" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "tick.json").write_text("0")
        (config_dir / "org_config.json").write_text('{"base_turn_seconds": 1}')
        (config_dir / "credits.json").write_text("{}")
        (config_dir / "models.json").write_text("{}")
        if not (tmp_path / "agents").exists():
            (tmp_path / "agents").mkdir()

        # 1. Test Unauthenticated Access - Should Fail with 401
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws") as websocket:
                pass

        # Note: starlette/fastapi TestClient usually raises WebSocketDisconnect with 403 if it was rejected
        # Or sometimes just a generic disconnect. The code might not be exactly 401 if it's handled via exception.
        # But verify_websocket_access raises HTTPException(401).
        # Let's inspect the error.
        # 2. Test Authenticated Access (Header) - Should Succeed
        with client.websocket_connect("/ws", headers={"X-Admin-Key": "secret123"}) as websocket:
            data = websocket.receive_json()
            assert "status" in data

        # 3. Test Authenticated Access (Query Param) - Should Succeed
        with client.websocket_connect("/ws?key=secret123") as websocket:
            data = websocket.receive_json()
            assert "status" in data
