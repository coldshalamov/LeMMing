from __future__ import annotations

import json
import logging
import json
import logging
from pathlib import Path
from typing import Any, cast

from .agents import DEFAULT_CREDITS, Agent, discover_agents
from .paths import get_config_dir

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path(__file__).parent / "config"

_org_config_cache: dict[str, Any] | None = None
_credits_cache: dict[str, Any] | None = None
_config_dir: Path = DEFAULT_CONFIG_DIR


def set_config_dir(base_path: Path | None) -> None:
    global _config_dir
    if base_path is None:
        _config_dir = DEFAULT_CONFIG_DIR
    else:
        _config_dir = get_config_dir(base_path)


def _load_json(filename: str) -> dict[str, Any]:
    path = _config_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing configuration file: {path}")
    with path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


def get_org_config(base_path: Path | None = None) -> dict[str, Any]:
    global _org_config_cache
    set_config_dir(base_path)
    if _org_config_cache is None:
        _org_config_cache = _load_json("org_config.json")
    return _org_config_cache


def _ensure_credit_entry(agent: Agent, credits: dict[str, Any]) -> None:
    if agent.name not in credits:
        credits[agent.name] = {}
    record = credits[agent.name]
    record.setdefault("model", agent.model.key)
    record.setdefault("max_credits", agent.credits.max_credits)
    record.setdefault("soft_cap", agent.credits.soft_cap)
    record.setdefault("credits_left", agent.credits.max_credits)
    record.setdefault("cost_per_action", 0.01)


def get_credits(base_path: Path | None = None, agents: list[Agent] | None = None) -> dict[str, Any]:
    global _credits_cache
    set_config_dir(base_path)
    if _credits_cache is None:
        _credits_cache = _load_json("credits.json")
    if agents:
        for agent in agents:
            _ensure_credit_entry(agent, _credits_cache)
    return _credits_cache


def derive_org_graph(base_path: Path) -> dict[str, dict[str, list[str]]]:
    agents = discover_agents(base_path)
    get_credits(base_path, agents)
    save_credits(base_path)  # Persist any new credit entries.

    agent_names = {agent.name for agent in agents}
    graph: dict[str, dict[str, list[str]]] = {}

    for agent in agents:
        readable = compute_virtual_inbox_sources(agent, agent_names)
        graph[agent.name] = {
            "can_read": readable,
            "tools": agent.permissions.tools,
        }
    return graph


def compute_virtual_inbox_sources(agent: Agent, agent_names: set[str]) -> list[str]:
    readable = agent.permissions.read_outboxes or []
    if readable == ["*"]:
        return sorted(name for name in agent_names if name != agent.name)
    return sorted(name for name in readable if name in agent_names and name != agent.name)


def save_derived_org_graph(base_path: Path) -> Path:
    graph = derive_org_graph(base_path)
    output_path = get_config_dir(base_path) / "org_graph_derived.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    return output_path


def get_agent_credits(agent: str, base_path: Path | None = None) -> dict[str, Any]:
    credits = get_credits(base_path)
    return cast(
        dict[str, Any],
        credits.get(
            agent,
            {
                "model": "gpt-4.1-mini",
                "cost_per_action": 0.01,
                "credits_left": 0.0,
            },
        ),
    )


def deduct_credits(agent: str, amount: float, base_path: Path | None = None) -> None:
    credits = get_credits(base_path)
    if agent not in credits:
        credits[agent] = {
            "model": "gpt-4.1-mini",
            "cost_per_action": amount,
            "credits_left": 0.0,
            "max_credits": DEFAULT_CREDITS["max_credits"],
            "soft_cap": DEFAULT_CREDITS["soft_cap"],
        }
    credits_left = credits[agent].get("credits_left", 0.0) - amount
    credits[agent]["credits_left"] = round(credits_left, 4)
    save_credits(base_path)


def save_credits(base_path: Path | None = None) -> None:
    path = _config_dir / "credits.json"
    _config_dir.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(get_credits(base_path), f, indent=2)


def reset_caches() -> None:
    global _org_config_cache, _credits_cache
    _org_config_cache = None
    _credits_cache = None
