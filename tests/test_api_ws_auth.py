
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from lemming.api import app


def test_websocket_auth(monkeypatch):
    # Set the admin key
    monkeypatch.setenv("LEMMING_ADMIN_KEY", "super-secret-key")

    client = TestClient(app)

    # 1. No key -> Expect failure (WebSocketDisconnect with 1008)
    # The server closes connection immediately, which TestClient raises as WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws") as websocket:
            pass
    assert exc.value.code == 1008

    # 2. Key in query param -> Expect success
    try:
        with client.websocket_connect("/ws?key=super-secret-key") as websocket:
            data = websocket.receive_json()
            assert "status" in data
    except Exception as e:
        pytest.fail(f"WebSocket connection failed with query param: {e}")

    # 3. Key in header -> Expect success
    try:
        with client.websocket_connect("/ws", headers={"X-Admin-Key": "super-secret-key"}) as websocket:
            data = websocket.receive_json()
            assert "status" in data
    except Exception as e:
        pytest.fail(f"WebSocket connection failed with header: {e}")
