from unittest.mock import MagicMock
from pathlib import Path
import pytest
from lemming.engine import run_tick

def test_cleanup_throttling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Verify that outbox cleanup is throttled based on 'outbox_cleanup_interval'.
    """
    # Mock dependencies
    monkeypatch.setattr("lemming.engine.discover_agents", lambda path: [])
    monkeypatch.setattr("lemming.engine.get_credits", lambda path, agents: {})

    # Mock config with interval = 2
    monkeypatch.setattr("lemming.engine.get_org_config", lambda path: {"outbox_cleanup_interval": 2})

    mock_cleanup = MagicMock(return_value=0)
    monkeypatch.setattr("lemming.engine.cleanup_old_outbox_entries", mock_cleanup)

    # Run tick 1 (1 % 2 != 0) -> Should SKIP cleanup
    run_tick(tmp_path, 1)

    # Run tick 2 (2 % 2 == 0) -> Should RUN cleanup
    run_tick(tmp_path, 2)

    # Run tick 3 (3 % 2 != 0) -> Should SKIP cleanup
    run_tick(tmp_path, 3)

    # Run tick 4 (4 % 2 == 0) -> Should RUN cleanup
    run_tick(tmp_path, 4)

    # Assert that it was called exactly 2 times (for ticks 2 and 4)
    assert mock_cleanup.call_count == 2, f"Expected 2 calls, got {mock_cleanup.call_count}"

    # Verify the arguments for the calls
    assert mock_cleanup.call_args_list[0].args[1] == 2
    assert mock_cleanup.call_args_list[1].args[1] == 4
