import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from lemming import api

@pytest.fixture
def client() -> TestClient:
    # Reset rate limits before each test
    api._request_timestamps.clear()
    return TestClient(api.app)

def test_admin_auth_not_configured(client: TestClient, tmp_path):
    """Verify sensitive endpoints are accessible when no admin key is set."""
    # Ensure LEMMING_ADMIN_KEY is not set
    with patch.dict(os.environ, {}, clear=False):
        if "LEMMING_ADMIN_KEY" in os.environ:
            del os.environ["LEMMING_ADMIN_KEY"]

        with patch("lemming.api.BASE_PATH", tmp_path), \
             patch("lemming.api.SECRETS_PATH", tmp_path / "secrets.json"):

            # Setup minimal environment for run_once (trigger_tick)
            config_dir = tmp_path / "lemming" / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "tick.json").write_text("0")
            (config_dir / "org_config.json").write_text('{"base_turn_seconds": 1}')
            (config_dir / "credits.json").write_text("{}")
            (config_dir / "models.json").write_text("{}")
            (tmp_path / "agents").mkdir()

            # Try trigger_tick
            resp = client.post("/api/engine/tick")
            # Should be 200 (success) because auth is disabled by default
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

            # Try update_engine_config
            resp = client.post("/api/engine/config", json={"openai_api_key": "test"})
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

def test_admin_auth_configured_success(client: TestClient, tmp_path):
    """Verify access is allowed with correct key when configured."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}), \
         patch("lemming.api.BASE_PATH", tmp_path), \
         patch("lemming.api.SECRETS_PATH", tmp_path / "secrets.json"):

        # Setup minimal environment
        config_dir = tmp_path / "lemming" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "tick.json").write_text("0")
        (config_dir / "org_config.json").write_text('{"base_turn_seconds": 1}')
        (config_dir / "credits.json").write_text("{}")
        (config_dir / "models.json").write_text("{}")
        if not (tmp_path / "agents").exists():
            (tmp_path / "agents").mkdir()

        headers = {"X-Admin-Key": "secret123"}

        # trigger_tick
        resp = client.post("/api/engine/tick", headers=headers)
        assert resp.status_code == 200

        # update_engine_config
        resp = client.post("/api/engine/config", json={"openai_api_key": "test"}, headers=headers)
        assert resp.status_code == 200

def test_admin_auth_configured_failure(client: TestClient, tmp_path):
    """Verify access is denied without correct key when configured."""
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}), \
         patch("lemming.api.BASE_PATH", tmp_path), \
         patch("lemming.api.SECRETS_PATH", tmp_path / "secrets.json"):

        # Setup minimal environment
        config_dir = tmp_path / "lemming" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "tick.json").write_text("0")
        (config_dir / "org_config.json").write_text('{"base_turn_seconds": 1}')
        (config_dir / "credits.json").write_text("{}")
        (config_dir / "models.json").write_text("{}")
        if not (tmp_path / "agents").exists():
            (tmp_path / "agents").mkdir()

        # No header
        resp = client.post("/api/engine/tick")
        assert resp.status_code == 401

        # Wrong header
        resp = client.post("/api/engine/tick", headers={"X-Admin-Key": "wrong"})
        assert resp.status_code == 401

        # update_engine_config
        resp = client.post("/api/engine/config", json={"openai_api_key": "test"})
        assert resp.status_code == 401
