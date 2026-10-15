import time
import json
from dataclasses import dataclass
from lemming.messages import OutboxEntry

@dataclass
class DummyEntry:
    agent: str
    kind: str
    created_at: str
    payload: dict

def format_outbox_context_original(entries, max_chars=8000000):
    lines = ["INCOMING MESSAGES:"]
    total = len(lines[0])
    for entry in entries:
        text = entry.payload.get("text", json.dumps(entry.payload))
        line = f"\n[{entry.created_at}] From {entry.agent} ({entry.kind}): {text}"
        if total + len(line) > max_chars:
            lines.append("\n... (truncated)")
            break
        lines.append(line)
        total += len(line)
    return "".join(lines)

def format_outbox_context_optimized(entries, max_chars=8000000):
    lines = ["INCOMING MESSAGES:"]
    total = len(lines[0])
    for entry in entries:
        text = entry.payload.get("text")
        if text is None:
            text = json.dumps(entry.payload)
        line = f"\n[{entry.created_at}] From {entry.agent} ({entry.kind}): {text}"
        if total + len(line) > max_chars:
            lines.append("\n... (truncated)")
            break
        lines.append(line)
        total += len(line)
    return "".join(lines)

entries = [
    DummyEntry("agent", "msg", "2023-01-01T00:00:00", {"text": "hello "*50, "other": "data "*50})
    for _ in range(10000)
]

start = time.time()
format_outbox_context_original(entries)
print(f"Original: {time.time() - start:.4f}s")

start = time.time()
format_outbox_context_optimized(entries)
print(f"Optimized: {time.time() - start:.4f}s")
