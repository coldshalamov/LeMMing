import json
from pathlib import Path
from fastapi.testclient import TestClient
from lemming import api

def test_engine_config_rate_limiting(tmp_path: Path):
    """Verify that update_engine_config is rate limited."""
    # Reset any existing rate limits for the test client
    api._request_timestamps.clear()

    api.BASE_PATH = tmp_path
    client = TestClient(api.app)

    # First few requests should succeed
    for _ in range(5):
        response = client.post("/api/engine/config", json={"openai_api_key": "sk-..."})
        assert response.status_code == 200

    # The 6th request should fail with 429 Too Many Requests (if limit is 5)
    response = client.post("/api/engine/config", json={"openai_api_key": "sk-..."})
    assert response.status_code == 429
    assert response.json()["detail"] == "Rate limit exceeded"

def test_engine_tick_rate_limiting(tmp_path: Path):
    """Verify that trigger_tick is rate limited."""
    api._request_timestamps.clear()

    # Mocking engine run components since we don't want to actually run the engine
    # We just want to check the rate limiter, which runs *before* the endpoint logic
    # But trigger_tick calls run_once which might fail if setup isn't done.
    # However, rate limiter dependency runs first.

    api.BASE_PATH = tmp_path
    client = TestClient(api.app)

    # Setup minimal environment to avoid 500 errors if rate limiter passes
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    # We don't need full setup if we expect the rate limiter to kick in eventually

    # NOTE: trigger_tick implementation tries to run the engine.
    # If we want to test rate limiting without setting up the whole engine,
    # we rely on the fact that 429 is raised by dependency *before* the handler code executes.
    # But for the *successful* calls, we might get 500s because environment is empty.
    # That's fine, as long as we distinguish 500 from 429.

    # To be cleaner, let's just make the calls.
    limit = 5

    for i in range(limit + 2):
        response = client.post("/api/engine/tick")
        if i < limit:
            # It might be 200 or 500 depending on engine state, but NOT 429
            assert response.status_code != 429
        else:
            assert response.status_code == 429
