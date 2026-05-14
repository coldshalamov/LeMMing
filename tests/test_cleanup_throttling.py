from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from lemming.engine import run_tick


def test_cleanup_throttling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock dependencies to isolate run_tick
    mock_discover_agents = MagicMock(return_value=[])
    monkeypatch.setattr("lemming.engine.discover_agents", mock_discover_agents)

    mock_get_credits = MagicMock()
    monkeypatch.setattr("lemming.engine.get_credits", mock_get_credits)

    mock_cleanup = MagicMock(return_value=0)
    monkeypatch.setattr("lemming.engine.cleanup_old_outbox_entries", mock_cleanup)

    # Mock configuration
    config = {
        "base_turn_seconds": 1.0,
        "max_outbox_age_ticks": 100,
        "outbox_cleanup_interval": 10,
    }
    monkeypatch.setattr("lemming.engine.get_org_config", lambda _: config)

    # Helper to prevent actual logging/event overhead during test
    monkeypatch.setattr("lemming.engine.logger", MagicMock())
    monkeypatch.setattr("lemming.engine.log_engine_event", MagicMock())

    base_path = tmp_path

    # Test tick 5: Should NOT cleanup (5 % 10 != 0)
    run_tick(base_path, tick=5)
    mock_cleanup.assert_not_called()

    # Test tick 10: Should cleanup (10 % 10 == 0)
    run_tick(base_path, tick=10)
    mock_cleanup.assert_called_once_with(base_path, 10, max_age_ticks=100)
    mock_cleanup.reset_mock()

    # Test tick 15: Should NOT cleanup
    run_tick(base_path, tick=15)
    mock_cleanup.assert_not_called()

    # Test tick 20: Should cleanup
    run_tick(base_path, tick=20)
    mock_cleanup.assert_called_once_with(base_path, 20, max_age_ticks=100)
