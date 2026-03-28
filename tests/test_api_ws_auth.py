import os
import unittest
from unittest.mock import patch

from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from lemming.api import app


class TestWebSocketAuth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_websocket_no_auth_required(self):
        # Ensure no key is set
        with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": ""}):
            with self.client.websocket_connect("/ws") as websocket:
                data = websocket.receive_json()
                self.assertIn("status", data)

    def test_websocket_auth_required_fail(self):
        # Set key
        with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret"}):
            # Attempt to connect without key. Should raise WebSocketDisconnect (403/1008)
            # If it succeeds (vulnerability), no exception is raised, and test fails.
            with self.assertRaises(WebSocketDisconnect):
                with self.client.websocket_connect("/ws") as websocket:
                    websocket.receive_json()

    def test_websocket_auth_success_query_param(self):
        with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret"}):
            with self.client.websocket_connect("/ws?key=secret") as websocket:
                data = websocket.receive_json()
                self.assertIn("status", data)

    def test_websocket_auth_success_header(self):
        with patch.dict(os.environ, {"LEMMING_ADMIN_KEY": "secret"}):
            with self.client.websocket_connect("/ws", headers={"X-Admin-Key": "secret"}) as websocket:
                data = websocket.receive_json()
                self.assertIn("status", data)
