from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .agents import Agent, discover_agents
from .logging_config import log_agent_action, log_engine_event
from .memory import get_memory_context, save_memory
from .messages import (
    OutboxEntry,
    cleanup_old_outbox_entries,
    collect_readable_outboxes,
    format_outbox_context,
    write_outbox_entry,
)
from .models import call_llm
from .org import deduct_credits, get_agent_credits, get_credits, get_org_config
from .paths import get_config_dir, get_logs_dir, get_tick_file
from .tools import ToolRegistry, ToolResult

logger = logging.getLogger(__name__)

SYSTEM_PREAMBLE = """You are a LeMMing agent operating in a multi-agent organization.
You communicate by writing entries to your outbox, which other agents can read.
You receive information by reading entries from other agents' outboxes.

You MUST respond with valid JSON in this exact format:
{
  "outbox_entries": [
    {
      "kind": "message|report|request|response|status",
      "payload": {"text": "...", ...optional additional fields...},
      "tags": ["optional", "tags"]
    }
  ],
  "tool_calls": [
    {
      "tool": "tool_name",
      "args": {...tool arguments...}
    }
  ],
  "memory_updates": [
    {
      "key": "memory_key",
      "value": {...any JSON value...}
    }
  ],
  "notes": "Optional free-form notes for activity logs"
}

All fields are optional but the response must be valid JSON.
If you have nothing to do, respond with: {"notes": "No action needed."}
"""


def load_tick(base_path: Path) -> int:
    tick_file = get_tick_file(base_path)
    if tick_file.exists():
        try:
            with tick_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return int(data.get("current_tick", 1))
        except Exception:  # pragma: no cover - defensive
            logger.warning("Could not parse tick file %s; defaulting to 1", tick_file)
    return 1


def persist_tick(base_path: Path, tick: int) -> None:
    tick_file = get_tick_file(base_path)
    tick_file.parent.mkdir(parents=True, exist_ok=True)
    with tick_file.open("w", encoding="utf-8") as f:
        json.dump({"current_tick": tick}, f, indent=2)


def compute_fire_point(agent: Agent) -> float:
    """Compute fire_point for intra-tick ordering.

    fire_point = (-phase_offset mod N) / N  ∈ [0, 1)

    This ensures deterministic execution order within a tick:
    - Agents with lower fire_point run first
    - Agents with same fire_point are ordered alphabetically by name
    """
    n = agent.schedule.run_every_n_ticks or 1
    if n == 1:
        return 0.0
    offset = agent.schedule.phase_offset % n
    return ((-offset) % n) / n


def should_run(agent: Agent, tick: int) -> bool:
    n = agent.schedule.run_every_n_ticks or 1
    offset = agent.schedule.phase_offset or 0
    return (tick % n) == (offset % n)


def get_firing_agents(agents: list[Agent], tick: int) -> list[Agent]:
    """Get agents that should fire this tick, in canonical order.

    Returns agents sorted by (fire_point, agent_name) for deterministic execution.
    """
    firing = []
    for agent in agents:
        if should_run(agent, tick):
            firing.append(agent)

    # Sort by (fire_point, agent_name) for deterministic ordering
    firing.sort(key=lambda a: (compute_fire_point(a), a.name))
    return firing


def _build_prompt(base_path: Path, agent: Agent, tick: int) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    messages.append({"role": "system", "content": SYSTEM_PREAMBLE})
    messages.append({"role": "system", "content": f"YOUR ROLE: {agent.title}\n\n{agent.instructions}"})

    memory_context = get_memory_context(base_path, agent.name)
    if memory_context and memory_context != "No memory entries.":
        messages.append({"role": "user", "content": f"YOUR MEMORY:\n{memory_context}"})

    incoming = collect_readable_outboxes(
        base_path,
        agent.name,
        agent.permissions.read_outboxes,
        limit=30,
    )
    messages.append({"role": "user", "content": format_outbox_context(incoming)})

    messages.append(
        {
            "role": "user",
            "content": (
                f"Current tick: {tick}\n"
                f"Available tools: {', '.join(agent.permissions.tools)}\n"
                "Provide your response as JSON following the schema."
            ),
        }
    )
    return messages


def _parse_llm_output(raw: str) -> dict[str, Any]:
    try:
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            body: list[str] = []
            in_block = False
            for line in lines:
                if line.startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    body.append(line)
            raw = "\n".join(body)
        data = json.loads(raw)
        return {
            "outbox_entries": data.get("outbox_entries", []),
            "tool_calls": data.get("tool_calls", []),
            "memory_updates": data.get("memory_updates", []),
            "notes": data.get("notes", ""),
        }
    except json.JSONDecodeError as exc:
        logger.error("LLM output was not valid JSON: %s", exc)
        logger.debug("Raw response: %s", raw)
        return {"outbox_entries": [], "tool_calls": [], "memory_updates": [], "notes": ""}


def _execute_tools(base_path: Path, agent: Agent, tool_calls: list[dict]) -> list[ToolResult]:
    results: list[ToolResult] = []
    allowed = set(agent.permissions.tools)
    for call in tool_calls:
        tool_name = call.get("tool")
        args = call.get("args", {}) or {}

        if tool_name not in allowed:
            results.append(ToolResult(False, "", f"Tool '{tool_name}' not permitted for {agent.name}"))
            continue

        tool = ToolRegistry.get(tool_name)
        if tool is None:
            results.append(ToolResult(False, "", f"Unknown tool: {tool_name}"))
            continue

        result = tool.execute(agent.name, base_path, **args)
        results.append(result)
    return results


def run_agent(base_path: Path, agent: Agent, tick: int) -> dict[str, Any]:
    start_time = time.time()

    credits_info = get_agent_credits(agent.name, base_path)
    credits_left = credits_info.get("credits_left", 0.0)
    cost_per_action = credits_info.get("cost_per_action", 0.01)

    if credits_left <= 0:
        logger.warning("Agent %s has no credits; skipping", agent.name)
        log_agent_action(
            base_path,
            agent.name,
            tick,
            "agent_skipped",
            reason="no_credits",
            credits_left=0.0,
        )
        return {"skipped": True, "reason": "no_credits"}

    # Build prompt and call LLM
    prompt = _build_prompt(base_path, agent, tick)
    llm_start = time.time()
    try:
        raw_output = call_llm(
            agent.model.key,
            prompt,
            temperature=agent.model.temperature,
            config_dir=get_config_dir(base_path),
        )
    except Exception as exc:
        logger.error("LLM call failed for agent %s: %s", agent.name, exc)
        log_agent_action(
            base_path,
            agent.name,
            tick,
            "llm_call_failed",
            error=str(exc),
            duration_ms=int((time.time() - llm_start) * 1000),
        )
        raise

    llm_duration_ms = int((time.time() - llm_start) * 1000)
    parsed = _parse_llm_output(raw_output)

    # Write outbox entries
    for entry_data in parsed.get("outbox_entries", []):
        entry = OutboxEntry.create(
            agent=agent.name,
            tick=tick,
            kind=entry_data.get("kind", "message"),
            payload=entry_data.get("payload", {}),
            tags=entry_data.get("tags", []),
            meta=entry_data.get("meta", {}),
        )
        write_outbox_entry(base_path, agent.name, entry)

    # Execute tools
    tool_results = _execute_tools(base_path, agent, parsed.get("tool_calls", []))

    # Update memory
    for update in parsed.get("memory_updates", []):
        key = update.get("key")
        if not key:
            continue
        save_memory(base_path, agent.name, key, update.get("value"))

    # Deduct credits
    deduct_credits(agent.name, cost_per_action, base_path)

    # Log notes to text file (for backward compatibility)
    notes = parsed.get("notes")
    if notes:
        log_dir = get_logs_dir(base_path, agent.name)
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "activity.log").open("a", encoding="utf-8") as f:
            f.write(f"[Tick {tick}] {notes}\n")

    # Log structured agent action
    total_duration_ms = int((time.time() - start_time) * 1000)
    log_agent_action(
        base_path,
        agent.name,
        tick,
        "agent_completed",
        duration_ms=total_duration_ms,
        llm_duration_ms=llm_duration_ms,
        outbox_count=len(parsed.get("outbox_entries", [])),
        tool_count=len(parsed.get("tool_calls", [])),
        memory_updates=len(parsed.get("memory_updates", [])),
        credits_left=credits_left - cost_per_action,
    )

    return {
        "outbox_entries": len(parsed.get("outbox_entries", [])),
        "tool_calls": len(parsed.get("tool_calls", [])),
        "tool_results": [asdict(result) for result in tool_results],
        "memory_updates": len(parsed.get("memory_updates", [])),
        "notes": notes,
        "duration_ms": total_duration_ms,
    }


def run_tick(base_path: Path, tick: int) -> dict[str, Any]:
    tick_start = time.time()
    logger.info("=== Tick %s ===", tick)
    log_engine_event("tick_started", tick=tick)

    results: dict[str, Any] = {}
    agents = discover_agents(base_path)
    get_credits(base_path, agents)

    # Get agents that should fire this tick in deterministic order
    firing_agents = get_firing_agents(agents, tick)
    log_engine_event(
        f"tick_{tick}_agents_firing",
        tick=tick,
        agent_count=len(firing_agents),
        agents=[a.name for a in firing_agents],
    )

    for agent in firing_agents:
        fire_point = compute_fire_point(agent)
        logger.info("Running agent: %s (fire_point=%.3f)", agent.name, fire_point)
        results[agent.name] = run_agent(base_path, agent, tick)

    # Cleanup old outbox entries
    removed = cleanup_old_outbox_entries(base_path, tick)
    if removed:
        logger.info("Cleaned up %s expired outbox entries", removed)
        log_engine_event("outbox_cleanup", tick=tick, entries_removed=removed)

    tick_duration_ms = int((time.time() - tick_start) * 1000)
    log_engine_event(
        "tick_completed",
        tick=tick,
        duration_ms=tick_duration_ms,
        agents_run=len(results),
    )

    return results


def run_once(base_path: Path, tick: int | None = None) -> dict[str, Any]:
    tick_to_run = tick if tick is not None else load_tick(base_path)
    results = run_tick(base_path, tick_to_run)
    persist_tick(base_path, tick_to_run + 1)
    return results


def run_forever(base_path: Path) -> None:
    config = get_org_config(base_path)
    base_turn_seconds = config.get("base_turn_seconds", 10)
    max_turns = config.get("max_turns")
    tick = load_tick(base_path)
    while True:
        run_tick(base_path, tick)
        persist_tick(base_path, tick + 1)
        if max_turns is not None and tick >= max_turns:
            break
        tick += 1
        time.sleep(base_turn_seconds)
