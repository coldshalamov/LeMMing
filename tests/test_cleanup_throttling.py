from pathlib import Path
from unittest.mock import MagicMock, patch

from lemming.engine import load_tick, run_tick


@patch("lemming.engine.get_org_config")
@patch("lemming.engine.discover_agents")
@patch("lemming.engine.get_credits")
@patch("lemming.engine.cleanup_old_outbox_entries")
@patch("lemming.engine.log_engine_event")
@patch("lemming.engine.get_firing_agents")
def test_cleanup_throttling(mock_get_firing, mock_log, mock_cleanup, mock_get_credits, mock_discover, mock_get_config):
    # Setup
    base_path = Path("/tmp/mock_path")
    mock_get_config.return_value = {
        "outbox_cleanup_interval": 10,
        "max_outbox_age_ticks": 100
    }
    mock_discover.return_value = []
    mock_get_firing.return_value = []

    # Tick 1: Should NOT run cleanup (1 % 10 != 0)
    run_tick(base_path, 1)
    mock_cleanup.assert_not_called()

    # Tick 9: Should NOT run cleanup
    run_tick(base_path, 9)
    mock_cleanup.assert_not_called()

    # Tick 10: SHOULD run cleanup
    mock_cleanup.return_value = 0
    run_tick(base_path, 10)
    mock_cleanup.assert_called_once_with(base_path, 10, max_age_ticks=100)
    mock_cleanup.reset_mock()

    # Tick 11: Should NOT run cleanup
    run_tick(base_path, 11)
    mock_cleanup.assert_not_called()

    # Tick 20: SHOULD run cleanup
    run_tick(base_path, 20)
    mock_cleanup.assert_called_once_with(base_path, 20, max_age_ticks=100)

@patch("lemming.engine.get_tick_file")
@patch("json.load")
def test_load_tick_eafp(mock_json_load, mock_get_tick_file):
    # Case 1: File exists and is valid
    mock_path = MagicMock()
    mock_get_tick_file.return_value = mock_path

    # Setup context manager for open
    mock_file_handle = MagicMock()
    mock_path.open.return_value.__enter__.return_value = mock_file_handle
    mock_json_load.return_value = {"current_tick": 42}

    assert load_tick(Path(".")) == 42

    # Case 2: FileNotFoundError
    mock_path.open.side_effect = FileNotFoundError
    assert load_tick(Path(".")) == 1

    # Case 3: Other exception (e.g. permission error) -> Should log and return 1
    mock_path.open.side_effect = PermissionError("Access denied")
    with patch("lemming.engine.logger") as mock_logger:
        assert load_tick(Path(".")) == 1
        mock_logger.warning.assert_called_once()
