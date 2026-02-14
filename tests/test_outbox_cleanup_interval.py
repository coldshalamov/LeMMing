from pathlib import Path
from unittest.mock import patch

import pytest

from lemming.engine import run_tick


@pytest.fixture
def mock_cleanup_old_outbox_entries():
    with patch("lemming.engine.cleanup_old_outbox_entries") as mock:
        yield mock


@pytest.fixture
def mock_get_org_config():
    with patch("lemming.engine.get_org_config") as mock:
        mock.return_value = {"max_outbox_age_ticks": 100}
        yield mock


@pytest.fixture
def mock_discover_agents():
    with patch("lemming.engine.discover_agents") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_get_credits():
    with patch("lemming.engine.get_credits") as mock:
        yield mock


@pytest.fixture
def mock_log_engine_event():
    with patch("lemming.engine.log_engine_event") as mock:
        yield mock


def test_cleanup_is_throttled(
    tmp_path: Path,
    mock_cleanup_old_outbox_entries,
    mock_get_org_config,
    mock_discover_agents,
    mock_get_credits,
    mock_log_engine_event,
):
    # Run for 20 ticks
    for tick in range(1, 21):
        run_tick(tmp_path, tick)

    # Assert it was called 2 times (tick 10 and 20)
    assert mock_cleanup_old_outbox_entries.call_count == 2
