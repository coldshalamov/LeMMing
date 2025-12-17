import json
from pathlib import Path

from lemming import org


def _write_config(base: Path, credits_value: float, label: str) -> None:
    config_dir = base / "lemming" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "credits.json").write_text(
        json.dumps({"agent": {"credits_left": credits_value}}), encoding="utf-8"
    )
    (config_dir / "org_config.json").write_text(
        json.dumps({"label": label}), encoding="utf-8"
    )


def test_config_cache_reset_between_base_paths(tmp_path: Path) -> None:
    base_one = tmp_path / "one"
    base_two = tmp_path / "two"
    _write_config(base_one, 1.0, "first")
    _write_config(base_two, 9.0, "second")

    org.reset_caches()

    credits_first = org.get_credits(base_one)
    assert credits_first["agent"]["credits_left"] == 1.0

    credits_second = org.get_credits(base_two)
    assert credits_second["agent"]["credits_left"] == 9.0

    config_second = org.get_org_config(base_two)
    assert config_second["label"] == "second"

    org.reset_caches()
