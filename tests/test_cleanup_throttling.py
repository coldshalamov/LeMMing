import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from lemming.engine import run_tick

def test_cleanup_throttling():
    base_path = Path("/tmp/mock")

    with patch("lemming.engine.get_org_config") as mock_config, \
         patch("lemming.engine.cleanup_old_outbox_entries") as mock_cleanup, \
         patch("lemming.engine.discover_agents") as mock_discover, \
         patch("lemming.engine.get_credits"), \
         patch("lemming.engine.log_engine_event"):

        # Configure mocks
        mock_config.return_value = {
            "outbox_cleanup_interval": 5,
            "max_outbox_age_ticks": 100
        }
        mock_discover.return_value = [] # No agents

        # Run ticks 1 to 10
        # Interval is 5.
        # Tick 1: 1 % 5 != 0 -> No cleanup
        # Tick 5: 5 % 5 == 0 -> Cleanup
        # Tick 6: 6 % 5 != 0 -> No cleanup
        # Tick 10: 10 % 5 == 0 -> Cleanup

        # Tick 1
        run_tick(base_path, 1)
        assert mock_cleanup.call_count == 0

        # Tick 4
        run_tick(base_path, 4)
        assert mock_cleanup.call_count == 0

        # Tick 5
        run_tick(base_path, 5)
        assert mock_cleanup.call_count == 1
        mock_cleanup.assert_called_with(base_path, 5, max_age_ticks=100)

        # Tick 6
        run_tick(base_path, 6)
        assert mock_cleanup.call_count == 1

        # Tick 10
        run_tick(base_path, 10)
        assert mock_cleanup.call_count == 2
        mock_cleanup.assert_called_with(base_path, 10, max_age_ticks=100)
