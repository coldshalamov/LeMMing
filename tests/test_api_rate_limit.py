
import pytest
from fastapi.testclient import TestClient

from lemming import api


@pytest.fixture
def client() -> TestClient:
    # Reset rate limits before each test
    api._request_timestamps.clear()
    return TestClient(api.app)

def test_rate_limit_update_engine_config(client: TestClient, tmp_path):
    """Verify rate limiting on update_engine_config."""
    # Mock SECRETS_PATH to avoid side effects
    old_secrets_path = api.SECRETS_PATH
    api.SECRETS_PATH = tmp_path / "secrets.json"

    try:
        url = "/api/engine/config"
        payload = {"openai_api_key": "test-key"}

        # We expect a limit of 5 (as per plan)
        # First 5 requests should succeed
        for i in range(5):
            resp = client.post(url, json=payload)
            assert resp.status_code == 200, f"Request {i+1} failed: {resp.text}"

        # 6th request should be rate limited
        resp = client.post(url, json=payload)
        assert resp.status_code == 429, "Rate limit not enforced on update_engine_config"

    finally:
        api.SECRETS_PATH = old_secrets_path

def test_rate_limit_trigger_tick(client: TestClient, tmp_path):
    """Verify rate limiting on trigger_tick."""
    # Mock BASE_PATH to avoid side effects on tick.json
    # The api.run_once needs a valid environment structure
    old_base_path = api.BASE_PATH
    api.BASE_PATH = tmp_path

    # Setup minimal environment for run_once
    config_dir = tmp_path / "lemming" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "tick.json").write_text("0")
    (config_dir / "org_config.json").write_text('{"base_turn_seconds": 1}')
    (config_dir / "credits.json").write_text("{}")
    (config_dir / "models.json").write_text("{}")
    (tmp_path / "agents").mkdir()

    try:
        url = "/api/engine/tick"

        # We expect a limit of 10 (as per plan)
        # First 10 requests should succeed
        for i in range(10):
            resp = client.post(url)
            assert resp.status_code == 200, f"Request {i+1} failed: {resp.text}"

        # 11th request should be rate limited
        resp = client.post(url)
        assert resp.status_code == 429, "Rate limit not enforced on trigger_tick"

    finally:
        api.BASE_PATH = old_base_path
