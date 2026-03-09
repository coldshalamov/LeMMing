
import pytest
from fastapi.testclient import TestClient

from lemming import api

@pytest.fixture
def client() -> TestClient:
    # Reset rate limits before each test
    api._request_timestamps.clear()
    return TestClient(api.app)

def test_rate_limit_scope_isolation(client: TestClient, tmp_path):
    """Verify that rate limits are scoped per endpoint/function."""
    # Mock SECRETS_PATH to avoid side effects
    old_secrets_path = api.SECRETS_PATH
    api.SECRETS_PATH = tmp_path / "secrets.json"

    try:
        # /api/messages has limit 10
        # /api/engine/config has limit 5

        # 1. Consume 5 requests on /api/messages
        # This fills the "IP bucket" with 5 timestamps if not scoped.
        for i in range(5):
            resp = client.post("/api/messages", json={
                "target": "manager",
                "text": "hello",
                "importance": "normal"
            })
            assert resp.status_code == 200, f"Message {i+1} failed"

        # 2. Try to access /api/engine/config
        # It has a limit of 5.
        # If scoped: 0 requests made for this scope -> Should Succeed.
        # If shared: 5 requests seen for this IP -> 5 >= 5 -> Should Fail (429).

        payload = {"openai_api_key": "test"}
        resp = client.post("/api/engine/config", json=payload)

        # We expect success (200) because quotas should be independent.
        assert resp.status_code == 200, f"Scoped rate limit failed! Got {resp.status_code}: {resp.text}"
    finally:
        api.SECRETS_PATH = old_secrets_path
