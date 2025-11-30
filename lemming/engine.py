from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .agents import Agent, discover_agents
from .file_dispatcher import cleanup_expired_messages
from .messaging import (
    Message,
    collect_incoming_messages,
    create_message,
    mark_message_processed,
    send_message,
)
from .models import call_llm
from .org import can_send, deduct_credits, get_agent_credits, get_org_config, reset_caches

logger = logging.getLogger(__name__)

SYSTEM_PREAMBLE = (
    "You are a LeMMing agent operating in a virtual organization. "
    "You receive messages by reading other agents' outboxes according to permissions. "
    "Respond strictly in JSON as described in your role instructions."
)


def _build_prompt(agent: Agent, messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    prompt_messages: list[dict[str, str]] = []
    prompt_messages.append({"role": "system", "content": SYSTEM_PREAMBLE})
    prompt_messages.append({"role": "system", "content": agent.instructions_text})
    if messages:
        formatted = "\n".join(
            [f"From {m['sender']} -> {m['receiver']} ({m['importance']}): {m['content']}" for m in messages]
        )
        prompt_messages.append({"role": "user", "content": f"Incoming messages:\n{formatted}"})
    else:
        prompt_messages.append({"role": "user", "content": "No new messages. Provide proactive update or idle."})
    return prompt_messages


def _parse_llm_output(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error("LLM output was not valid JSON: %s", raw)
        return {"messages": [], "notes": "Failed to parse response"}


def _agent_should_run(agent: Agent, current_turn: int, force: bool = False) -> bool:
    if force:
        return True
    return current_turn % max(agent.org_speed_multiplier, 1) == 0


def _run_agent(
    base_path: Path, agent: Agent, current_turn: int, incoming_payloads: list[dict[str, Any]]
) -> dict[str, Any]:
    credits_info = get_agent_credits(agent.name, base_path)
    credits_left = credits_info.get("credits_left", 0.0)
    cost_per_action = credits_info.get("cost_per_action", 0.0)

    if credits_left <= 0:
        logger.warning("Skipping %s; no credits left", agent.name)
        return {}

    prompt = _build_prompt(agent, incoming_payloads)
    raw_output = call_llm(agent.model_key, prompt, temperature=0.2, config_dir=base_path / "lemming" / "config")
    parsed = _parse_llm_output(raw_output)
    outgoing = parsed.get("messages", []) or []

    for item in outgoing:
        receiver = item.get("to")
        content = item.get("content", "")
        importance = item.get("importance", "normal")
        ttl_turns = item.get("ttl_turns", 24)
        if receiver and can_send(agent.name, receiver, base_path):
            msg = create_message(
                agent.name,
                receiver,
                content,
                importance=importance,
                ttl_turns=ttl_turns,
                current_turn=current_turn,
            )
            send_message(base_path, msg)
        else:
            logger.warning("%s attempted to send to unauthorized receiver %s", agent.name, receiver)

    deduct_credits(agent.name, cost_per_action, base_path)

    for payload in incoming_payloads:
        try:
            msg = Message(**payload)
            mark_message_processed(base_path, msg)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to mark message processed: %s", exc)

    notes = parsed.get("notes")
    if notes:
        log_dir = agent.path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "activity.log").open("a", encoding="utf-8") as f:
            f.write(f"Turn {current_turn}: {notes}\n")

    return parsed


def run_once(base_path: Path, current_turn: int) -> None:
    logger.info("Running turn %s", current_turn)
    reset_caches()
    agents = discover_agents(base_path)
    config = get_org_config(base_path)
    summary_every = config.get("summary_every_n_turns", 12)

    for agent in agents:
        force_run = agent.name == "manager" and current_turn % max(summary_every, 1) == 0
        if not _agent_should_run(agent, current_turn, force=force_run):
            continue

        incoming_messages = collect_incoming_messages(base_path, agent.name, current_turn)
        incoming_payloads = [asdict(m) for m in incoming_messages]
        parsed = _run_agent(base_path, agent, current_turn, incoming_payloads)

        if agent.name == "manager" and force_run:
            summary = parsed.get("notes", "") if isinstance(parsed, dict) else ""
            log_dir = agent.path / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            summary_path = log_dir / f"summary_{current_turn}.txt"
            summary_path.write_text(summary, encoding="utf-8")
            print(f"[Manager Summary Turn {current_turn}] {summary}")

    cleanup_expired_messages(base_path, current_turn)


def run_forever(base_path: Path) -> None:
    config = get_org_config(base_path)
    base_turn_seconds = config.get("base_turn_seconds", 10)
    max_turns = config.get("max_turns")
    current_turn = 1
    while True:
        run_once(base_path, current_turn)
        if max_turns is not None and isinstance(max_turns, int) and current_turn >= max_turns:
            break
        current_turn += 1
        time.sleep(base_turn_seconds)
