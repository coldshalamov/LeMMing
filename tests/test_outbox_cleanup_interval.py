from unittest.mock import patch

from lemming.engine import run_tick


def test_outbox_cleanup_interval(tmp_path):
    base_path = tmp_path / "lemming"
    base_path.mkdir()

    # Mocking necessary components to avoid side effects
    with (
        patch("lemming.engine.get_org_config") as mock_config,
        patch("lemming.engine.cleanup_old_outbox_entries") as mock_cleanup,
        patch("lemming.engine.discover_agents") as mock_discover,
        patch("lemming.engine.get_credits"),
        patch("lemming.engine.get_firing_agents") as mock_firing,
        patch("lemming.engine.log_engine_event"),
    ):

        mock_config.return_value = {"max_outbox_age_ticks": 100}
        mock_discover.return_value = []
        mock_firing.return_value = []

        # Run ticks 1-9
        for i in range(1, 10):
            run_tick(base_path, i)

        # Should NOT call cleanup
        assert mock_cleanup.call_count == 0

        # Run tick 10
        run_tick(base_path, 10)
        # Should call cleanup
        assert mock_cleanup.call_count == 1

        # Run tick 11
        run_tick(base_path, 11)
        # Should NOT call cleanup (still 1)
        assert mock_cleanup.call_count == 1

        # Run tick 20
        run_tick(base_path, 20)
        # Should call cleanup (now 2)
        assert mock_cleanup.call_count == 2
