from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .engine import run_forever, run_once
from .org import reset_caches

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_RESUME_TEMPLATE = """Name: {name}
Role: {role}
Description: {description}

[INSTRUCTIONS]
{instructions}

[CONFIG]
{config}
"""


def write_resume(path: Path, name: str, role: str, description: str, instructions: str, config: dict) -> None:
    text = BASE_RESUME_TEMPLATE.format(
        name=name,
        role=role,
        description=description,
        instructions=instructions.strip(),
        config=json.dumps(config, indent=2),
    )
    path.write_text(text, encoding="utf-8")


def ensure_agent_dirs(agent_path: Path) -> None:
    for sub in ["outbox", "memory", "logs", "config"]:
        (agent_path / sub).mkdir(parents=True, exist_ok=True)


def bootstrap(base_path: Path) -> None:
    config_dir = base_path / "lemming" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    defaults = {
        "org_chart.json": {
            "human": {"send_to": ["manager"], "read_from": ["manager"]},
            "manager": {
                "send_to": ["planner", "hr", "coder_01", "janitor", "human"],
                "read_from": ["planner", "hr", "coder_01", "janitor", "human"],
            },
            "planner": {"send_to": ["coder_01", "manager"], "read_from": ["manager", "coder_01"]},
            "hr": {"send_to": ["manager"], "read_from": ["manager"]},
            "coder_01": {"send_to": ["planner", "manager"], "read_from": ["planner"]},
            "janitor": {"send_to": ["manager"], "read_from": ["manager", "planner", "coder_01", "hr"]},
        },
        "credits.json": {
            "manager": {"model": "gpt-4.1-mini", "cost_per_action": 0.01, "credits_left": 100.0},
            "planner": {"model": "gpt-4.1-mini", "cost_per_action": 0.01, "credits_left": 100.0},
            "hr": {"model": "gpt-4.1-mini", "cost_per_action": 0.01, "credits_left": 100.0},
            "coder_01": {"model": "gpt-4.1", "cost_per_action": 0.03, "credits_left": 200.0},
            "janitor": {"model": "gpt-4.1-mini", "cost_per_action": 0.005, "credits_left": 50.0},
        },
        "org_config.json": {"base_turn_seconds": 10, "summary_every_n_turns": 12, "max_turns": None},
        "models.json": {
            "gpt-4.1": {"provider": "openai", "model_name": "gpt-4.1"},
            "gpt-4.1-mini": {"provider": "openai", "model_name": "gpt-4.1-mini"},
        },
    }

    for filename, content in defaults.items():
        path = config_dir / filename
        if not path.exists():
            path.write_text(json.dumps(content, indent=2), encoding="utf-8")
            logger.info("Created default config %s", path)

    # Agent template
    template_dir = base_path / "agents" / "agent_template"
    ensure_agent_dirs(template_dir)
    if not (template_dir / "resume.txt").exists():
        template_resume = """Name: TEMPLATE_AGENT
Role: Generic worker agent
Description: A generic LeMMing agent created from the template. Customize this resume for specific roles.

[INSTRUCTIONS]
You are a LeMMing agent. Follow your role description and respond with clear, structured outputs.
You receive messages from other agents and produce replies or actions.
Always respond in JSON following the protocol described in your CONFIG.

[CONFIG]
{
  "model": "gpt-4.1-mini",
  "org_speed_multiplier": 1,
  "send_to": [],
  "read_from": [],
  "max_credits": 50.0,
  "priority": "normal"
}
"""
        (template_dir / "resume.txt").write_text(template_resume, encoding="utf-8")
        logger.info("Created agent template resume")

    # Create human agent directory
    human_dir = base_path / "agents" / "human"
    ensure_agent_dirs(human_dir)
    if not (human_dir / "resume.txt").exists():
        human_resume = """Name: HUMAN
Role: Human user
Description: The human user who interacts with the organization.

[INSTRUCTIONS]
You are the human user. This is a placeholder for the human operator.

[CONFIG]
{
  "model": "none",
  "org_speed_multiplier": 1,
  "send_to": ["manager"],
  "read_from": ["manager"],
  "max_credits": 999999.0,
  "priority": "highest"
}
"""
        (human_dir / "resume.txt").write_text(human_resume, encoding="utf-8")
        logger.info("Created human agent directory")

    # Concrete agents
    agent_defs = {
        "manager": {
            "role": "Organization manager and user interface",
            "description": "Top-level agent that communicates with the human user and coordinates all other agents.",
            "instructions": """You are the Manager agent in the LeMMing organization.
You do NOT write code or perform low-level tasks directly.
Your jobs are:
- Interpret high-level user goals (from logs or future stdin integration).
- Communicate with Planner, HR, and other agents only through messages.
- Periodically summarize org status in a concise, human-readable way.
- When you respond, always output JSON:

{
  \"messages\": [
    {
      \"to\": \"<agent_name>\",
      \"content\": \"<text>\",
      \"importance\": \"normal\",
      \"ttl_turns\": 12
    }
  ],
  \"notes\": \"<free-form summary for logs>\"
}
""",
            "config": {
                "model": "gpt-4.1-mini",
                "org_speed_multiplier": 1,
                "send_to": ["planner", "hr", "coder_01", "janitor"],
                "read_from": ["planner", "hr", "coder_01", "janitor"],
                "max_credits": 100.0,
                "priority": "high",
            },
        },
        "planner": {
            "role": "Breaks goals into tasks and coordinates execution",
            "description": "Planner decomposes objectives, assigns work to coder_01, and reports progress to manager.",
            "instructions": """You are the Planner agent.
Analyze objectives from the Manager, break them into actionable tasks, and delegate to coder_01.
Report progress and blockers back to the Manager. Keep messages concise and actionable.
Always respond with JSON payloads containing messages and notes.
""",
            "config": {
                "model": "gpt-4.1-mini",
                "org_speed_multiplier": 1,
                "send_to": ["coder_01", "manager"],
                "read_from": ["manager", "coder_01"],
                "max_credits": 100.0,
                "priority": "high",
            },
        },
        "hr": {
            "role": "HR and org growth advisor",
            "description": "HR proposes new agents and monitors morale and capacity.",
            "instructions": """You are the HR agent.
Monitor the organization for staffing gaps and suggest new agents using the template.
You do not create agents directly but propose configurations to the Manager.
Always respond with JSON containing messages and notes.
""",
            "config": {
                "model": "gpt-4.1-mini",
                "org_speed_multiplier": 2,
                "send_to": ["manager"],
                "read_from": ["manager"],
                "max_credits": 100.0,
                "priority": "normal",
            },
        },
        "coder_01": {
            "role": "Primary coding agent",
            "description": "Implements tasks defined by Planner and reports technical status.",
            "instructions": """You are coder_01.
Implement and explain code-level tasks assigned by the Planner.
If you need clarification, ask the Planner. Provide progress updates for the Manager when appropriate.
Always respond with JSON containing messages and notes.
""",
            "config": {
                "model": "gpt-4.1",
                "org_speed_multiplier": 1,
                "send_to": ["planner", "manager"],
                "read_from": ["planner"],
                "max_credits": 200.0,
                "priority": "high",
            },
        },
        "janitor": {
            "role": "Cleanup and maintenance",
            "description": "Janitor suggests cleanup of expired or excessive messages and files.",
            "instructions": """You are the Janitor agent.
Inspect the organization for stale or excessive messages and propose cleanup actions.
You cannot delete files directly; request actions via messages to the Manager.
Always respond with JSON containing messages and notes.
""",
            "config": {
                "model": "gpt-4.1-mini",
                "org_speed_multiplier": 3,
                "send_to": ["manager"],
                "read_from": ["manager", "planner", "coder_01", "hr"],
                "max_credits": 50.0,
                "priority": "normal",
            },
        },
    }

    for name, info in agent_defs.items():
        agent_dir = base_path / "agents" / name
        ensure_agent_dirs(agent_dir)
        resume_path = agent_dir / "resume.txt"
        if not resume_path.exists():
            write_resume(
                resume_path,
                name=info.get("name", name).upper(),
                role=info["role"],
                description=info["description"],
                instructions=info["instructions"],
                config=info["config"],
            )
            logger.info("Created resume for %s", name)

    reset_caches()


def send_message_cmd(base_path: Path, agent: str, message: str, importance: str = "normal") -> None:
    """Send a message from human to an agent."""
    from .messaging import create_message, send_message as send_msg

    msg = create_message(sender="human", receiver=agent, content=message, importance=importance, current_turn=0)
    send_msg(base_path, msg)
    print(f"✉️  Message sent to {agent}")


def view_inbox(base_path: Path) -> None:
    """View messages sent to human from agents."""
    from .messaging import collect_incoming_messages

    messages = collect_incoming_messages(base_path, "human", current_turn=999999)

    if not messages:
        print("📭 No messages in your inbox")
        return

    print(f"\n📬 You have {len(messages)} message(s):\n")
    for i, msg in enumerate(messages, 1):
        print(f"[{i}] From: {msg.sender}")
        print(f"    Importance: {msg.importance}")
        print(f"    Content: {msg.content}")
        print(f"    Time: {msg.timestamp}")
        print()


def chat_mode(base_path: Path, agent: str = "manager") -> None:
    """Interactive chat mode with an agent."""
    from .messaging import collect_incoming_messages, create_message, mark_message_processed, send_message as send_msg

    print(f"💬 Chat mode with {agent}. Type 'exit' or 'quit' to leave.\n")

    while True:
        message = input(f"You → {agent}: ").strip()

        if message.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        if not message:
            continue

        # Send message
        msg = create_message(sender="human", receiver=agent, content=message, current_turn=0)
        send_msg(base_path, msg)

        # Wait a moment and check for replies
        import time

        time.sleep(1)

        # Collect responses
        responses = collect_incoming_messages(base_path, "human", current_turn=999999)
        if responses:
            for resp in responses:
                if resp.sender == agent:
                    print(f"{agent} → You: {resp.content}\n")
                    mark_message_processed(base_path, resp)
        else:
            print(f"(No immediate response from {agent})\n")


def show_status(base_path: Path) -> None:
    """Show org status including credits and agents."""
    from .agents import discover_agents
    from .org import get_credits

    agents = discover_agents(base_path)
    credits = get_credits(base_path)

    print("\n🏢 LeMMing Organization Status\n")
    print(f"{'Agent':<15} {'Model':<20} {'Credits':<10} {'Speed':<5}")
    print("=" * 55)

    for agent in agents:
        credit_info = credits.get(agent.name, {})
        credits_left = credit_info.get("credits_left", 0.0)
        model = credit_info.get("model", agent.model_key)
        print(f"{agent.name:<15} {model:<20} {credits_left:<10.2f} {agent.org_speed_multiplier}x")

    print()


def show_logs(base_path: Path, agent: str, lines: int = 20) -> None:
    """Show recent logs for an agent."""
    log_file = base_path / "agents" / agent / "logs" / "activity.log"

    if not log_file.exists():
        print(f"No logs found for {agent}")
        return

    with log_file.open("r") as f:
        all_lines = f.readlines()

    recent = all_lines[-lines:]
    print(f"\n📝 Recent logs for {agent} (last {lines} lines):\n")
    for line in recent:
        print(line.rstrip())


def inspect_agent(base_path: Path, agent: str) -> None:
    """Show detailed information about an agent."""
    from .agents import load_agent
    from .org import get_agent_credits, get_read_from, get_send_to

    try:
        ag = load_agent(base_path, agent)
    except FileNotFoundError:
        print(f"Agent '{agent}' not found")
        return

    credits = get_agent_credits(agent, base_path)
    send_to = get_send_to(agent, base_path)
    read_from = get_read_from(agent, base_path)

    print(f"\n🔍 Agent: {ag.name}\n")
    print(f"Role: {ag.role}")
    print(f"Description: {ag.description}")
    print(f"Model: {ag.model_key}")
    print(f"Speed Multiplier: {ag.org_speed_multiplier}x")
    print(f"Max Credits: {ag.max_credits}")
    print(f"Credits Left: {credits.get('credits_left', 0.0):.2f}")
    print(f"Can send to: {', '.join(send_to) if send_to else 'none'}")
    print(f"Can read from: {', '.join(read_from) if read_from else 'none'}")
    print()


def top_up_credits(base_path: Path, agent: str, amount: float) -> None:
    """Add credits to an agent."""
    from .org import deduct_credits, get_agent_credits, save_credits

    # Deduct negative amount = add credits
    deduct_credits(agent, -amount, base_path)
    save_credits(base_path)

    new_credits = get_agent_credits(agent, base_path).get("credits_left", 0.0)
    print(f"💰 Added {amount} credits to {agent}. New balance: {new_credits:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LeMMing CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("bootstrap", help="Bootstrap default configs and agents")
    sub.add_parser("run", help="Run the engine indefinitely")
    sub.add_parser("run-once", help="Run a single engine turn")

    # Human interaction commands
    send_parser = sub.add_parser("send", help="Send a message to an agent")
    send_parser.add_argument("agent", help="Agent to send message to")
    send_parser.add_argument("message", help="Message content")
    send_parser.add_argument("--importance", default="normal", choices=["low", "normal", "high", "urgent"])

    sub.add_parser("inbox", help="View messages sent to you")

    chat_parser = sub.add_parser("chat", help="Interactive chat with an agent")
    chat_parser.add_argument("--agent", default="manager", help="Agent to chat with (default: manager)")

    # Status and inspection commands
    sub.add_parser("status", help="Show organization status")

    logs_parser = sub.add_parser("logs", help="Show agent logs")
    logs_parser.add_argument("agent", help="Agent name")
    logs_parser.add_argument("--lines", type=int, default=20, help="Number of lines to show")

    inspect_parser = sub.add_parser("inspect", help="Inspect agent details")
    inspect_parser.add_argument("agent", help="Agent name")

    topup_parser = sub.add_parser("top-up", help="Add credits to an agent")
    topup_parser.add_argument("agent", help="Agent name")
    topup_parser.add_argument("amount", type=float, help="Amount of credits to add")

    args = parser.parse_args()
    base_path = Path(__file__).resolve().parent.parent

    if args.command == "bootstrap":
        bootstrap(base_path)
    elif args.command == "run":
        run_forever(base_path)
    elif args.command == "run-once":
        run_once(base_path, current_turn=1)
    elif args.command == "send":
        send_message_cmd(base_path, args.agent, args.message, args.importance)
    elif args.command == "inbox":
        view_inbox(base_path)
    elif args.command == "chat":
        chat_mode(base_path, args.agent)
    elif args.command == "status":
        show_status(base_path)
    elif args.command == "logs":
        show_logs(base_path, args.agent, args.lines)
    elif args.command == "inspect":
        inspect_agent(base_path, args.agent)
    elif args.command == "top-up":
        top_up_credits(base_path, args.agent, args.amount)


if __name__ == "__main__":
    main()
