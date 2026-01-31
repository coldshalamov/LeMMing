import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from lemming import api


@pytest.fixture
def client() -> TestClient:
    api._request_timestamps.clear()
    return TestClient(api.app)


def test_send_message_auth_behavior(client: TestClient, tmp_path):
    """Verify send_message auth behavior under different configurations."""

    # Common setup
    config_dir = tmp_path / "lemming" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "tick.json").write_text("0")

    # 1. Test: No Admin Key (Default Local Mode) -> Should allow access
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("lemming.api.BASE_PATH", tmp_path),
        patch("lemming.api.SECRETS_PATH", tmp_path / "secrets.json"),
    ):

        # Ensure key is gone
        if "LEMMING_ADMIN_KEY" in os.environ:
            del os.environ["LEMMING_ADMIN_KEY"]

        resp = client.post("/api/messages", json={"target": "agent1", "text": "Hello", "importance": "normal"})
        assert resp.status_code == 200, "Should allow access when no admin key is set"

    # 2. Test: Admin Key Set, No Header -> Should deny access (401)
    with (
        patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}),
        patch("lemming.api.BASE_PATH", tmp_path),
        patch("lemming.api.SECRETS_PATH", tmp_path / "secrets.json"),
    ):

        resp = client.post("/api/messages", json={"target": "agent1", "text": "Hello", "importance": "normal"})
        # Currently this is expected to fail (it returns 200) until we fix it
        # So we assert 401 to demonstrate the fix later
        assert resp.status_code == 401, "Should deny access when admin key is set but header is missing"

    # 3. Test: Admin Key Set, Correct Header -> Should allow access (200)
    with (
        patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}),
        patch("lemming.api.BASE_PATH", tmp_path),
        patch("lemming.api.SECRETS_PATH", tmp_path / "secrets.json"),
    ):

        resp = client.post(
            "/api/messages",
            json={"target": "agent1", "text": "Hello", "importance": "normal"},
            headers={"X-Admin-Key": "secret123"},
        )

        assert resp.status_code == 200, "Should allow access with correct admin key"
