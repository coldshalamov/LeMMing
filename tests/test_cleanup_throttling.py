from unittest.mock import patch

from lemming.engine import run_tick


def test_cleanup_throttling_default(tmp_path):
    """Verify that cleanup is throttled by default (interval=10)."""

    # Mock dependencies to isolate run_tick logic
    with (
        patch("lemming.engine.cleanup_old_outbox_entries") as mock_cleanup,
        patch("lemming.engine.discover_agents", return_value=[]),
        patch("lemming.engine.get_credits"),
        patch("lemming.engine.persist_tick"),
        patch("lemming.engine.log_engine_event"),
        patch("lemming.engine.get_org_config", return_value={}),
    ):

        # Tick 1: 1 % 10 != 0 -> No cleanup
        run_tick(tmp_path, 1)
        mock_cleanup.assert_not_called()

        # Tick 9: 9 % 10 != 0 -> No cleanup
        run_tick(tmp_path, 9)
        mock_cleanup.assert_not_called()

        # Tick 10: 10 % 10 == 0 -> Cleanup
        run_tick(tmp_path, 10)
        mock_cleanup.assert_called_once()

        # Tick 11: 11 % 10 != 0 -> No cleanup
        mock_cleanup.reset_mock()
        run_tick(tmp_path, 11)
        mock_cleanup.assert_not_called()


def test_cleanup_throttling_configured(tmp_path):
    """Verify that cleanup respects configured interval."""

    config = {"outbox_cleanup_interval": 5}

    with (
        patch("lemming.engine.cleanup_old_outbox_entries") as mock_cleanup,
        patch("lemming.engine.discover_agents", return_value=[]),
        patch("lemming.engine.get_credits"),
        patch("lemming.engine.persist_tick"),
        patch("lemming.engine.log_engine_event"),
        patch("lemming.engine.get_org_config", return_value=config),
    ):

        # Tick 1: 1 % 5 != 0 -> No cleanup
        run_tick(tmp_path, 1)
        mock_cleanup.assert_not_called()

        # Tick 5: 5 % 5 == 0 -> Cleanup
        run_tick(tmp_path, 5)
        mock_cleanup.assert_called_once()

        # Tick 10: 10 % 5 == 0 -> Cleanup
        mock_cleanup.reset_mock()
        run_tick(tmp_path, 10)
        mock_cleanup.assert_called_once()
