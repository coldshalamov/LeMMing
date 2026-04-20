import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from lemming.engine import run_tick

@pytest.fixture
def mock_cleanup():
    with patch("lemming.engine.cleanup_old_outbox_entries") as mock:
        yield mock

@pytest.fixture
def mock_config():
    with patch("lemming.engine.get_org_config") as mock:
        yield mock

@pytest.fixture
def mock_dependencies():
    with patch("lemming.engine.discover_agents", return_value=[]), \
         patch("lemming.engine.get_credits"), \
         patch("lemming.engine.log_engine_event"), \
         patch("lemming.engine.logger"), \
         patch("lemming.engine.compute_fire_point", return_value=0.0):
        yield

def test_cleanup_runs_only_on_interval(mock_cleanup, mock_config, mock_dependencies, tmp_path):
    # Configure mock config to have interval of 5
    mock_config.return_value = {
        "outbox_cleanup_interval": 5,
        "max_outbox_age_ticks": 100
    }

    base_path = tmp_path

    # Tick 1: Should NOT run (1 % 5 != 0)
    run_tick(base_path, tick=1)
    mock_cleanup.assert_not_called()

    # Tick 4: Should NOT run (4 % 5 != 0)
    run_tick(base_path, tick=4)
    mock_cleanup.assert_not_called()

    # Tick 5: Should RUN (5 % 5 == 0)
    run_tick(base_path, tick=5)
    mock_cleanup.assert_called_once()

    # Tick 6: Should NOT run
    mock_cleanup.reset_mock()
    run_tick(base_path, tick=6)
    mock_cleanup.assert_not_called()

    # Tick 10: Should RUN
    run_tick(base_path, tick=10)
    mock_cleanup.assert_called_once()

def test_cleanup_defaults_to_10(mock_cleanup, mock_config, mock_dependencies, tmp_path):
    # Missing config key
    mock_config.return_value = {
        "max_outbox_age_ticks": 100
    }

    base_path = tmp_path

    # Tick 5: Should NOT run (default is 10)
    run_tick(base_path, tick=5)
    mock_cleanup.assert_not_called()

    # Tick 10: Should RUN
    run_tick(base_path, tick=10)
    mock_cleanup.assert_called_once()
