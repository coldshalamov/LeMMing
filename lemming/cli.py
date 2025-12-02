from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .agents import discover_agents, load_agent
from .config_validation import validate_everything
from .engine import run_forever, run_once
from .org import derive_org_graph, save_derived_org_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def list_agents_cmd(base_path: Path) -> None:
    agents = discover_agents(base_path)
    print(f"\n{'Name':<20} {'Title':<30} {'Schedule':<20} {'Model':<20}")
    print("=" * 95)
    for agent in agents:
        schedule = f"every {agent.schedule.run_every_n_ticks} (offset {agent.schedule.phase_offset})"
        print(f"{agent.name:<20} {agent.title:<30} {schedule:<20} {agent.model.key:<20}")
    print(f"\nTotal: {len(agents)} agents")


def show_agent_cmd(base_path: Path, name: str) -> None:
    try:
        agent = load_agent(base_path, name)
    except FileNotFoundError:
        print(f"Agent '{name}' not found")
        return

    print(f"\n{'='*60}\nAgent: {agent.name}\n{'='*60}")
    print(f"Title: {agent.title}")
    print(f"Description: {agent.short_description}")
    if agent.workflow_description:
        print(f"Workflow: {agent.workflow_description}")
    print(f"Model: {agent.model.key} (temp={agent.model.temperature}, max_tokens={agent.model.max_tokens})")
    print(
        f"Schedule: every {agent.schedule.run_every_n_ticks} ticks (offset={agent.schedule.phase_offset})"
    )
    print(f"Readable outboxes: {', '.join(agent.permissions.read_outboxes)}")
    print(f"Tools: {', '.join(agent.permissions.tools)}")
    print("\nInstructions preview:\n" + "-" * 40)
    preview = agent.instructions[:600]
    if len(agent.instructions) > 600:
        preview += "..."
    print(preview)


def derive_graph_cmd(base_path: Path) -> None:
    graph = derive_org_graph(base_path)
    print("\nDerived Organization Graph\n" + "=" * 50)
    for agent, info in sorted(graph.items()):
        can_read = info.get("can_read", [])
        tools = info.get("tools", [])
        print(f"\n{agent}:")
        print(f"  Can read: {', '.join(can_read) if can_read else '(none)'}")
        print(f"  Tools: {', '.join(tools) if tools else '(none)'}")
    saved = save_derived_org_graph(base_path)
    print(f"\nSaved to: {saved}")


def migrate_resumes_cmd(base_path: Path) -> None:
    from scripts.migrate_resumes import main as migrate_main

    migrate_main()


def main() -> None:
    parser = argparse.ArgumentParser(description="LeMMing CLI")
    parser.add_argument("command", help="Command to run")
    parser.add_argument("arg", nargs="?", help="Optional argument")
    parser.add_argument("--base-path", default=Path.cwd(), type=Path, help="Repository base path")
    args = parser.parse_args()

    base_path: Path = args.base_path

    if args.command == "run":
        run_forever(base_path)
    elif args.command == "run-once":
        tick = int(args.arg or 1)
        run_once(base_path, tick)
    elif args.command == "validate":
        errors = validate_everything(base_path)
        if errors:
            print("Validation errors:")
            for err in errors:
                print(f" - {err}")
        else:
            print("All configs and resumes are valid.")
    elif args.command == "list-agents":
        list_agents_cmd(base_path)
    elif args.command == "show-agent":
        if not args.arg:
            parser.error("show-agent requires an agent name")
        show_agent_cmd(base_path, args.arg)
    elif args.command == "derive-graph":
        derive_graph_cmd(base_path)
    elif args.command == "migrate-resumes":
        migrate_resumes_cmd(base_path)
    else:
        parser.error(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
