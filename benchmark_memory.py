import os
import json
import time
from pathlib import Path

def setup_fake_memory(base_path, agent_name, num_entries):
    mem_dir = Path(base_path) / "agents" / agent_name / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    for i in range(num_entries):
        with open(mem_dir / f"mem_{i:04d}.json", "w") as f:
            json.dump({"value": f"value for {i}"}, f)

from lemming.memory import get_memory_summary, get_memory_context

def test_original(base_path, agent_name):
    start = time.time()
    res = get_memory_context(Path(base_path), agent_name, 20)
    end = time.time()
    return end - start, res

def test_optimized(base_path, agent_name, max_items=20):
    start = time.time()
    mem_dir = Path(base_path) / "agents" / agent_name / "memory"
    try:
        with os.scandir(mem_dir) as it:
            entries = [entry for entry in it if entry.is_file() and entry.name.endswith(".json")]
    except FileNotFoundError:
        return "No memory entries."

    if not entries:
        return "No memory entries."

    entries.sort(key=lambda e: e.name)

    lines = []
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

    res = "\n".join(lines)
    end = time.time()
    return end - start, res

if __name__ == "__main__":
    setup_fake_memory("/tmp/lemming_bench", "bench_agent", 1000)

    # Warmup
    test_original("/tmp/lemming_bench", "bench_agent")
    test_optimized("/tmp/lemming_bench", "bench_agent")

    t_orig = sum(test_original("/tmp/lemming_bench", "bench_agent")[0] for _ in range(10)) / 10
    t_opt = sum(test_optimized("/tmp/lemming_bench", "bench_agent")[0] for _ in range(10)) / 10

    print(f"Original: {t_orig:.6f}s")
    print(f"Optimized: {t_opt:.6f}s")
    print(f"Speedup: {t_orig / t_opt:.2f}x")
