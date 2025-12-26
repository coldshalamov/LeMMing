from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .agents import discover_agents, load_agent
from .bootstrap import bootstrap as run_bootstrap
from .config_validation import validate_everything
from .engine import load_tick, run_forever, run_once
from .memory import get_memory_summary
from .messages import OutboxEntry, read_outbox_entries, write_outbox_entry
from .org import derive_org_graph, get_agent_credits, get_credits, save_derived_org_graph
from .paths import get_logs_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HUMAN_AGENT_NAME = "human"


def list_agents_cmd(base_path: Path) -> None:
    agents = discover_agents(base_path)
    if not agents:
        print("No agents found. Run `python -m lemming.cli bootstrap` to create one.")
        return

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
    save_derived_org_graph(base_path)
    print("\nDerived Organization Graph\n" + "=" * 50)
    for agent, info in sorted(graph.items()):
        can_read = info.get("can_read", [])
        tools = info.get("tools", [])
        print(f"\n{agent}:")
        print(f"  Can read: {', '.join(can_read) if can_read else '(none)'}")
        print(f"  Tools: {', '.join(tools) if tools else '(none)'}")


def migrate_resumes_cmd() -> None:
    from scripts.migrate_resumes import main as migrate_main

    migrate_main()


def bootstrap_cmd(base_path: Path) -> None:
    result = run_bootstrap(base_path)
    if result["created_configs"]:
        print(f"Created config files: {', '.join(result['created_configs'])}")
    if result["template_created"]:
        print("Created agents/agent_template")
    if result["example_created"]:
        print("Created agents/example_planner")
    if result["logs_dir_created"]:
        print("Created logs/ directory")
    if not any(result.values()):
        print("Everything already set up. Nothing to do.")


def status_cmd(base_path: Path) -> None:
    tick = load_tick(base_path)
    agents = discover_agents(base_path)
    credits = get_credits(base_path, agents)
    total_credits = sum(entry.get("credits_left", 0.0) for entry in credits.values())

    print("LeMMing status:\n" + "=" * 40)
    print(f"Current tick: {tick}")
    print(f"Agents discovered: {len(agents)}")
    print(f"Total credits remaining: {total_credits}")

    if agents:
        print("\nPer-agent credits:")
        for agent in agents:
            info = get_agent_credits(agent.name, base_path)
            print(f"- {agent.name}: {info.get('credits_left', 0.0)} (model {info.get('model')})")


def inspect_cmd(base_path: Path, name: str, outbox_limit: int = 5) -> None:
    try:
        agent = load_agent(base_path, name)
    except FileNotFoundError:
        print(f"Agent '{name}' not found")
        return

    print(f"Agent: {agent.name}\nTitle: {agent.title}\nModel: {agent.model.key}\n")

    entries = read_outbox_entries(base_path, agent.name, limit=outbox_limit)
    if entries:
        print("Recent outbox entries:")
        for entry in entries:
            preview = entry.payload.get("text") or json.dumps(entry.payload)
            print(f"- [tick {entry.tick}] ({entry.kind}) {preview}")
    else:
        print("No outbox entries found.")

    memory = get_memory_summary(base_path, agent.name)
    if memory:
        print("\nMemory summary:")
        for key, value in memory.items():
            print(f"- {key}: {value}")
    else:
        print("\nNo memory recorded.")


def logs_cmd(base_path: Path, name: str, lines: int) -> None:
    log_dir = get_logs_dir(base_path, name)
    log_path = log_dir / "structured.jsonl"
    if not log_path.exists():
        print(f"No structured log file found for agent '{name}'. It will be created on first run.")
        return

    content = log_path.read_text(encoding="utf-8").splitlines()
    for line in content[-lines:]:
        print(line)


def send_cmd(base_path: Path, target: str, message: str, importance: str = "normal") -> None:
    """Send a message from human to an agent."""
    # Verify target agent exists
    try:
        load_agent(base_path, target)
    except FileNotFoundError:
        print(f"Error: Agent '{target}' not found")
        sys.exit(1)

    tick = load_tick(base_path)
    entry = OutboxEntry.create(
        agent=HUMAN_AGENT_NAME,
        tick=tick,
        kind="message",
        payload={
            "text": message,
            "importance": importance,
            "target": target,
        },
        tags=["human-originated"],
    )
    write_outbox_entry(base_path, HUMAN_AGENT_NAME, entry)
    print(f"✉️  Message sent to '{target}' at tick {tick}")
    print(f"    Content: {message}")


def inbox_cmd(base_path: Path, agent: str | None = None, limit: int = 20) -> None:
    """View inbox (messages from agents)."""
    if agent:
        # Show specific agent's outbox
        try:
            load_agent(base_path, agent)
        except FileNotFoundError:
            print(f"Error: Agent '{agent}' not found")
            sys.exit(1)

        entries = read_outbox_entries(base_path, agent, limit=limit)
        print(f"\n📬 Outbox for '{agent}':")
    else:
        # Show all recent messages from all agents
        agents = discover_agents(base_path)
        entries = []
        for ag in agents:
            if ag.name == HUMAN_AGENT_NAME:
                continue
            agent_entries = read_outbox_entries(base_path, ag.name, limit=limit)
            entries.extend(agent_entries)

        # Sort by tick and created_at, most recent first
        entries.sort(key=lambda e: (e.tick, e.created_at), reverse=True)
        entries = entries[:limit]
        print("\n📥 Recent messages from all agents:")

    if not entries:
        print("  (no messages)")
        return

    for entry in entries:
        text = entry.payload.get("text", json.dumps(entry.payload))
        # Truncate long messages
        if len(text) > 100:
            text = text[:97] + "..."
        importance = entry.payload.get("importance", "normal")
        importance_marker = "❗" if importance == "high" else " "
        print(f"{importance_marker} [Tick {entry.tick}] {entry.agent} ({entry.kind}): {text}")


def chat_cmd(base_path: Path, target_agent: str | None = None) -> None:
    """Interactive chat mode with an agent."""
    target = target_agent if target_agent else "example_planner"

    # Verify target agent exists
    try:
        load_agent(base_path, target)
    except FileNotFoundError:
        print(f"Error: Agent '{target}' not found")
        print("Available agents:")
        list_agents_cmd(base_path)
        sys.exit(1)

    print(f"💬 Chat mode with '{target}' (type 'quit' or 'exit' to leave, 'tick' to advance)")
    print("─" * 60)

    while True:
        try:
            user_input = input(f"\nYou → {target}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting chat.")
            break

        if user_input.lower() in ("quit", "exit"):
            break
        elif user_input.lower() == "tick":
            print("⏱️  Advancing tick...")
            result = run_once(base_path)
            agents_run = list(result.keys())
            if agents_run:
                print(f"   Agents that ran: {', '.join(agents_run)}")
            else:
                print("   No agents ran this tick")
            # Show recent messages from target agent
            entries = read_outbox_entries(base_path, target, limit=3)
            if entries:
                print(f"\n   Recent messages from '{target}':")
                for entry in entries:
                    text = entry.payload.get("text", json.dumps(entry.payload))
                    if len(text) > 150:
                        text = text[:147] + "..."
                    print(f"   [{entry.kind}] {text}")
        elif user_input:
            send_cmd(base_path, target, user_input)
            # Auto-advance tick so agent processes message
            print("⏱️  Advancing tick for agent to respond...")
            result = run_once(base_path)
            if target in result:
                print(f"   '{target}' processed your message")
                # Show the response
                entries = read_outbox_entries(base_path, target, limit=3)
                if entries:
                    print(f"\n   {target} → You:")
                    for entry in entries[:1]:  # Show most recent
                        text = entry.payload.get("text", json.dumps(entry.payload))
                        print(f"   {text}")
            else:
                print(f"   '{target}' did not run this tick (check schedule)")


def serve_cmd(host: str, port: int) -> None:
    try:
        import uvicorn
    except ImportError:  # pragma: no cover - optional dependency
        print("uvicorn is not installed. Install with `pip install .[api]`.")
        sys.exit(1)

    uvicorn.run("lemming.api:app", host=host, port=port, reload=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LeMMing CLI")
    parser.add_argument("--base-path", default=Path.cwd(), type=Path, help="Repository base path")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("run", help="Run the engine continuously")

    run_once_parser = subparsers.add_parser("run-once", help="Run a single tick")
    run_once_parser.add_argument("--tick", type=int, help="Tick to run; defaults to persisted tick")

    subparsers.add_parser("validate", help="Validate configs and resumes")
    subparsers.add_parser("bootstrap", help="Create missing configs and agents")
    subparsers.add_parser("list-agents", help="List all agents")

    show_parser = subparsers.add_parser("show-agent", help="Show agent details")
    show_parser.add_argument("name", help="Agent name")

    derive_parser = subparsers.add_parser("derive-graph", help="Derive organization graph")
    derive_parser.add_argument("--save", action="store_true", help="(deprecated; graph saved automatically)")

    subparsers.add_parser("migrate-resumes", help="Migrate resume files")
    subparsers.add_parser("status", help="Show high-level status")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect an agent's state")
    inspect_parser.add_argument("name", help="Agent name")
    inspect_parser.add_argument("--outbox", type=int, default=5, help="Number of outbox entries to show")

    logs_parser = subparsers.add_parser("logs", help="Show recent agent logs")
    logs_parser.add_argument("name", help="Agent name")
    logs_parser.add_argument("--lines", type=int, default=20, help="Number of log lines to show")

    serve_parser = subparsers.add_parser("serve", help="Run the API server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind")

    send_parser = subparsers.add_parser("send", help="Send a message to an agent")
    send_parser.add_argument("target", help="Target agent name")
    send_parser.add_argument("message", help="Message text to send")
    send_parser.add_argument("--importance", default="normal", choices=["normal", "high"], help="Message importance")

    inbox_parser = subparsers.add_parser("inbox", help="View messages from agents")
    inbox_parser.add_argument("--agent", help="Show outbox from a specific agent")
    inbox_parser.add_argument("--limit", type=int, default=20, help="Number of messages to show")

    chat_parser = subparsers.add_parser("chat", help="Interactive chat with an agent")
    chat_parser.add_argument("--agent", help="Agent to chat with (default: example_planner)")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    base_path: Path = args.base_path

    if args.command == "run":
        run_forever(base_path)
    elif args.command == "run-once":
        run_once(base_path, args.tick)
    elif args.command == "validate":
        errors = validate_everything(base_path)
        if errors:
            print(f"Validation errors ({len(errors)}):")
            for err in errors:
                print(f" - {err}")
            print("Fix the issues above and re-run `python -m lemming.cli validate`.")
            sys.exit(1)
        print("All configs and resumes are valid.")
    elif args.command == "bootstrap":
        bootstrap_cmd(base_path)
    elif args.command == "list-agents":
        list_agents_cmd(base_path)
    elif args.command == "show-agent":
        show_agent_cmd(base_path, args.name)
    elif args.command == "derive-graph":
        derive_graph_cmd(base_path)
    elif args.command == "migrate-resumes":
        migrate_resumes_cmd()
    elif args.command == "status":
        status_cmd(base_path)
    elif args.command == "inspect":
        inspect_cmd(base_path, args.name, outbox_limit=args.outbox)
    elif args.command == "logs":
        logs_cmd(base_path, args.name, args.lines)
    elif args.command == "serve":
        serve_cmd(args.host, args.port)
    elif args.command == "send":
        send_cmd(base_path, args.target, args.message, args.importance)
    elif args.command == "inbox":
        inbox_cmd(base_path, args.agent, args.limit)
    elif args.command == "chat":
        chat_cmd(base_path, args.agent)
    else:  # pragma: no cover - parser enforces valid commands
        parser.error(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
