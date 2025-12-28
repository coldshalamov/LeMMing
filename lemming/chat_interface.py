import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from lemming.messages import OutboxEntry
from lemming.paths import get_outbox_dir

BASE_PATH = Path(__file__).parent.parent


def send_message(content: str):
    """Send a message from human to manager."""
    outbox_dir = get_outbox_dir(BASE_PATH, "human")

    entry = OutboxEntry.create(
        agent="human", tick=0, kind="task", payload={"content": content, "to": ["manager"]}, tags=["chat"]
    )

    filename = f"msg_{int(time.time()*1000)}.json"
    with open(outbox_dir / filename, "w", encoding="utf-8") as f:
        json.dump(entry.to_dict(), f, indent=2)

    print("\n[Human] -> Sent to Manager")


def get_latest_manager_reply(since_ts: float) -> Any:
    """Check manager outbox for new messages."""
    manager_outbox = get_outbox_dir(BASE_PATH, "manager")
    if not manager_outbox.exists():
        return None

    # Get all json files
    files = list(manager_outbox.glob("*.json"))
    messages = []

    for p in files:
        try:
            # Check mtime first for speed
            if p.stat().st_mtime < since_ts:
                continue

            with open(p, encoding="utf-8") as f:
                data = json.load(f)

            # Filter for messages relevant to human
            # Ideally manager explicitly addresses human, or we just show all manager output for now
            payload = data.get("payload", {})
            recipients = payload.get("to", [])

            # If explicit recipients exist, only show if 'human' is in it
            if recipients and "human" not in recipients:
                continue

            messages.append(data)
        except Exception:
            continue

    if not messages:
        return None

    # Sort by timestamp
    messages.sort(key=lambda x: x["created_at"])
    return messages[-1]


async def chat_loop():
    print("🤖 LeMMing Manager Chat")
    print("-----------------------")
    print("Type your message and press Enter. Ctrl+C to exit.")

    last_seen_ts = time.time()

    while True:
        user_input = input("\nYou > ")
        if not user_input.strip():
            continue

        send_message(user_input)

        print("Waiting for reply...", end="", flush=True)

        # Poll for reply
        waiting = True
        while waiting:
            reply = get_latest_manager_reply(last_seen_ts)
            if reply:
                print("\r" + " " * 20 + "\r", end="")  # Clear waiting message
                content = reply.get("payload", {}).get("content", "No content")
                print(f"Manager > {content}")
                last_seen_ts = time.time()
                waiting = False
            else:
                print(".", end="", flush=True)
                await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        print("\nGoodbye!")
