import os
import json
import time
from pathlib import Path

from lemming.paths import get_memory_dir
from lemming.memory import get_memory_context, get_memory_summary

def get_memory_context_optimized(base_path: Path, agent_name: str, max_items: int = 20) -> str:
    """
    Return a text block summarizing the agent's memory suitable for prompt injection.
    May truncate or summarize if there are many keys/values.
    """
    memory_dir = get_memory_dir(base_path, agent_name)
    lines: list[str] = []

    try:
        with os.scandir(memory_dir) as it:
            # We filter for .json files and collect only max_items if we are just slicing them
            # However, for stable tests, we might want to sort them. The old code just iterates dict keys
            # and dict keys come from os.scandir order, which is arbitrary. So if we sort, we change behavior?
            # Let's check if there is a sorting requirement.

            # Old code just does: summary = get_memory_summary... for idx, (k,v) in enumerate(summary.items())
            # get_memory_summary parses ALL files then returns dict.
            # If we just need top max_items, we can sort the entries.
            entries = []
            for entry in it:
                if entry.is_file() and entry.name.endswith(".json"):
                    entries.append(entry)

            if not entries:
                return "No memory entries."

            entries.sort(key=lambda e: e.name) # deterministic

            for idx, entry in enumerate(entries):
                if idx >= max_items:
                    lines.append("... (truncated)")
                    break

                key = entry.name[:-5]
                try:
                    with open(entry.path, encoding="utf-8") as f:
                        data = json.load(f)
                    value = data.get("value")
                except Exception as exc:
                    value = None

                display = value
                try:
                    display = json.dumps(value)
                except Exception:
                    display = str(value)
                lines.append(f"{key}: {display}")

            return "\n".join(lines)
    except FileNotFoundError:
        return "No memory entries."

def test_same_output():
    base_path = Path("/tmp/lemming_bench")
    agent_name = "bench_agent"

    orig = get_memory_context(base_path, agent_name, 20)
    opt = get_memory_context_optimized(base_path, agent_name, 20)

    print("Original (first 100 chars):", repr(orig[:100]))
    print("Optimized (first 100 chars):", repr(opt[:100]))

if __name__ == "__main__":
    test_same_output()
