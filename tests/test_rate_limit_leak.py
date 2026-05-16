from unittest.mock import Mock, patch

import pytest

from lemming import api


@pytest.mark.asyncio
async def test_rate_limiter_memory_cap():
    """Verify that the rate limiter dictionary is capped at MAX_RATE_LIMIT_CLIENTS."""
    # Clear existing state
    api._request_timestamps.clear()

    # Mock the limit to a small number for testing
    with patch("lemming.api.MAX_RATE_LIMIT_CLIENTS", 100):
        limiter = api.rate_limiter(limit=10, window=60)

        # Simulate requests from more unique IPs than the limit
        unique_ips = 150
        for i in range(unique_ips):
            mock_request = Mock()
            mock_request.client.host = f"10.0.0.{i}"

            # Call the dependency
            await limiter(mock_request)

        # Verify cap: dictionary size should be equal to the limit (100)
        assert len(api._request_timestamps) == 100

        # Verify that the last added IP is present (FIFO eviction of OLD IPs)
        assert "10.0.0.149:global" in api._request_timestamps
        # Verify that the first added IP is gone
        assert "10.0.0.0:global" not in api._request_timestamps
