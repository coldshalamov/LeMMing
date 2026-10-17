import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from lemming import api


@pytest.fixture
def client() -> TestClient:
    api._request_timestamps.clear()
    return TestClient(api.app)

def test_get_engine_config_auth_configured_failure(client: TestClient, tmp_path):
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}), \
         patch("lemming.api.BASE_PATH", tmp_path), \
         patch("lemming.api.SECRETS_PATH", tmp_path / "secrets.json"):

        resp = client.get("/api/engine/config")
        assert resp.status_code == 401

def test_get_engine_config_auth_configured_success(client: TestClient, tmp_path):
    with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret123"}), \
         patch("lemming.api.BASE_PATH", tmp_path), \
         patch("lemming.api.SECRETS_PATH", tmp_path / "secrets.json"):

        headers = {"X-Admin-Key": "secret123"}
        resp = client.get("/api/engine/config", headers=headers)
        assert resp.status_code == 200
