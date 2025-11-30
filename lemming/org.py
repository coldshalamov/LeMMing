from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path(__file__).parent / "config"

_org_chart_cache: Dict[str, Any] | None = None
_org_config_cache: Dict[str, Any] | None = None
_credits_cache: Dict[str, Any] | None = None
_config_dir: Path = DEFAULT_CONFIG_DIR


def set_config_dir(base_path: Path | None) -> None:
    global _config_dir
    if base_path is None:
        _config_dir = DEFAULT_CONFIG_DIR
    else:
        _config_dir = base_path / "lemming" / "config"
    logger.debug("Config directory set to %s", _config_dir)


def _load_json(filename: str) -> Dict[str, Any]:
    path = _config_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing configuration file: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_org_chart(base_path: Path | None = None) -> Dict[str, Any]:
    global _org_chart_cache
    set_config_dir(base_path)
    if _org_chart_cache is None:
        _org_chart_cache = _load_json("org_chart.json")
    return _org_chart_cache


def get_org_config(base_path: Path | None = None) -> Dict[str, Any]:
    global _org_config_cache
    set_config_dir(base_path)
    if _org_config_cache is None:
        _org_config_cache = _load_json("org_config.json")
    return _org_config_cache


def get_credits(base_path: Path | None = None) -> Dict[str, Any]:
    global _credits_cache
    set_config_dir(base_path)
    if _credits_cache is None:
        _credits_cache = _load_json("credits.json")
    return _credits_cache


def can_send(sender: str, receiver: str, base_path: Path | None = None) -> bool:
    chart = get_org_chart(base_path)
    return receiver in chart.get(sender, {}).get("send_to", [])


def get_read_from(agent: str, base_path: Path | None = None) -> list[str]:
    chart = get_org_chart(base_path)
    return list(chart.get(agent, {}).get("read_from", []))


def get_send_to(agent: str, base_path: Path | None = None) -> list[str]:
    chart = get_org_chart(base_path)
    return list(chart.get(agent, {}).get("send_to", []))


def get_agent_credits(agent: str, base_path: Path | None = None) -> Dict[str, Any]:
    credits = get_credits(base_path)
    return credits.get(agent, {})


def deduct_credits(agent: str, amount: float, base_path: Path | None = None) -> None:
    credits = get_credits(base_path)
    if agent not in credits:
        logger.warning("Agent %s not found in credits; initializing", agent)
        credits[agent] = {"model": "gpt-4.1-mini", "cost_per_action": amount, "credits_left": 0.0}
    credits_left = credits[agent].get("credits_left", 0.0)
    credits_left -= amount
    credits[agent]["credits_left"] = round(credits_left, 4)
    logger.debug("Deducted %.4f credits from %s; remaining %.4f", amount, agent, credits_left)
    save_credits(base_path)


def save_credits(base_path: Path | None = None) -> None:
    path = _config_dir / "credits.json"
    credits = get_credits(base_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(credits, f, indent=2)
    logger.info("Saved credits to %s", path)


def reset_caches() -> None:
    global _org_chart_cache, _org_config_cache, _credits_cache
    _org_chart_cache = None
    _org_config_cache = None
    _credits_cache = None
