from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .agents import Agent, discover_agents
from .memory import get_memory_context, save_memory
from .messages import (
    OutboxEntry,
    cleanup_old_outbox_entries,
    collect_readable_outboxes,
    format_outbox_context,
    write_outbox_entry,
)
from .models import call_llm
from .org import deduct_credits, get_agent_credits, get_org_config
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


def should_run(agent: Agent, tick: int) -> bool:
    """
    Determine if an agent should run on a given tick.

    Args:
        agent: The agent to check
        tick: Current tick number

    Returns:
        True if the agent should run this tick, False otherwise

    The agent runs when: (tick % run_every_n_ticks) == (phase_offset % run_every_n_ticks)
    """
    n = agent.schedule.run_every_n_ticks or 1
    offset = agent.schedule.phase_offset or 0
    return (tick % n) == (offset % n)


def _build_prompt(base_path: Path, agent: Agent, tick: int) -> list[dict[str, str]]:
    """
    Build the prompt messages for an agent's LLM call.

    Includes:
    - System preamble with JSON schema
    - Agent role and instructions
    - Agent memory context
    - Incoming messages from readable outboxes
    - Current tick and available tools

    Args:
        base_path: Base path of the LeMMing installation
        agent: The agent to build the prompt for
        tick: Current tick number

    Returns:
        List of message dictionaries for the LLM
    """
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
    """
    Parse LLM JSON output, handling both raw JSON and markdown code blocks.

    Args:
        raw: Raw LLM response string

    Returns:
        Dictionary with keys: outbox_entries, tool_calls, memory_updates, notes
        Returns empty structure if parsing fails
    """
    try:
        raw = raw.strip()
        # Handle markdown code blocks
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
    """
    Execute tool calls for an agent, respecting permissions.

    Args:
        base_path: Base path of the LeMMing installation
        agent: The agent executing the tools
        tool_calls: List of tool call dicts with 'tool' and 'args' keys

    Returns:
        List of ToolResult objects
    """
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
    """
    Run a single agent for one tick.

    Performs the following:
    1. Checks agent has sufficient credits
    2. Builds prompt with agent context
    3. Calls LLM and parses response
    4. Writes outbox entries
    5. Executes tool calls
    6. Updates agent memory
    7. Deducts credits
    8. Logs activity

    Args:
        base_path: Base path of the LeMMing installation
        agent: The agent to run
        tick: Current tick number

    Returns:
        Dictionary with execution statistics
    """
    credits_info = get_agent_credits(agent.name, base_path)
    credits_left = credits_info.get("credits_left", 0.0)
    cost_per_action = credits_info.get("cost_per_action", 0.01)

    if credits_left <= 0:
        logger.warning("Agent %s has no credits; skipping", agent.name)
        return {"skipped": True, "reason": "no_credits"}

    prompt = _build_prompt(base_path, agent, tick)
    raw_output = call_llm(
        agent.model.key,
        prompt,
        temperature=agent.model.temperature,
        config_dir=base_path / "lemming" / "config",
    )
    parsed = _parse_llm_output(raw_output)

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

    tool_results = _execute_tools(base_path, agent, parsed.get("tool_calls", []))

    for update in parsed.get("memory_updates", []):
        key = update.get("key")
        if not key:
            continue
        save_memory(base_path, agent.name, key, update.get("value"))

    deduct_credits(agent.name, cost_per_action, base_path)

    notes = parsed.get("notes")
    if notes:
        log_dir = agent.path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "activity.log").open("a", encoding="utf-8") as f:
            f.write(f"[Tick {tick}] {notes}\n")

    return {
        "outbox_entries": len(parsed.get("outbox_entries", [])),
        "tool_calls": len(parsed.get("tool_calls", [])),
        "tool_results": [asdict(result) for result in tool_results],
        "memory_updates": len(parsed.get("memory_updates", [])),
        "notes": notes,
    }


def run_tick(base_path: Path, tick: int) -> dict[str, Any]:
    """
    Execute one tick of the engine, running all scheduled agents.

    Args:
        base_path: Base path of the LeMMing installation
        tick: Current tick number

    Returns:
        Dictionary mapping agent names to their execution results
    """
    logger.info("=== Tick %s ===", tick)
    results: dict[str, Any] = {}
    agents = discover_agents(base_path)
    for agent in agents:
        if not should_run(agent, tick):
            continue
        logger.info("Running agent: %s", agent.name)
        results[agent.name] = run_agent(base_path, agent, tick)

    removed = cleanup_old_outbox_entries(base_path, tick)
    if removed:
        logger.info("Cleaned up %s expired outbox entries", removed)
    return results


def run_once(base_path: Path, tick: int = 1) -> dict[str, Any]:
    """
    Run the engine for exactly one tick (useful for testing).

    Args:
        base_path: Base path of the LeMMing installation
        tick: Tick number to run (default: 1)

    Returns:
        Execution results from run_tick
    """
    return run_tick(base_path, tick)


def run_forever(base_path: Path) -> None:
    config = get_org_config(base_path)
    base_turn_seconds = config.get("base_turn_seconds", 10)
    max_turns = config.get("max_turns")
    tick = 1
    while True:
        run_tick(base_path, tick)
        if max_turns is not None and tick >= max_turns:
            break
        tick += 1
        time.sleep(base_turn_seconds)
