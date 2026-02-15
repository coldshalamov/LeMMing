import logging
from pathlib import Path
from unittest.mock import patch

from lemming.engine import OUTBOX_CLEANUP_INTERVAL, run_tick

# Set up logging to avoid noise during tests
logging.basicConfig(level=logging.INFO)

def test_cleanup_frequency(tmp_path: Path):
    """Verify that cleanup_old_outbox_entries is throttled to run only at specific intervals
    defined by OUTBOX_CLEANUP_INTERVAL.
    """
    base_path = tmp_path
    (base_path / "agents").mkdir()
    (base_path / "shared").mkdir()

    # Create config dir
    config_dir = base_path / "lemming" / "config"
    config_dir.mkdir(parents=True)

    # Create required config files
    (config_dir / "org_config.json").write_text('{}')
    (config_dir / "credits.json").write_text('{}')
    (config_dir / "tick.json").write_text('{"current_tick": 1}')

    with patch("lemming.engine.cleanup_old_outbox_entries") as mock_cleanup:
        mock_cleanup.return_value = 0

        # Verify constant is as expected
        assert OUTBOX_CLEANUP_INTERVAL == 10

        # Run for ticks 1 to 20
        # Expected cleanup at tick 10 and 20
        for tick in range(1, 21):
            run_tick(base_path, tick)

        # Verify it was called exactly 2 times
        assert mock_cleanup.call_count == 2

        # Verify calls were made with correct ticks
        calls = mock_cleanup.call_args_list
        assert calls[0][0][1] == 10  # First arg is base_path, second is tick
        assert calls[1][0][1] == 20
