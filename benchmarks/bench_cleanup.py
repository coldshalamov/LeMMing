import time
import os
import shutil
from pathlib import Path
from lemming.messages import cleanup_old_outbox_entries, OutboxEntry, write_outbox_entry

def setup_benchmark_env(base_path: Path, num_agents: int, msgs_per_agent: int):
    if base_path.exists():
        shutil.rmtree(base_path)
    base_path.mkdir()

    (base_path / "agents").mkdir()

    print(f"Generating {num_agents} agents with {msgs_per_agent} messages each...")
    for i in range(num_agents):
        agent_name = f"agent_{i}"
        (base_path / "agents" / agent_name).mkdir()

        # Create messages
        for j in range(msgs_per_agent):
            # Mix of old and new messages
            tick = 100 if j % 2 == 0 else 1000
            entry = OutboxEntry.create(
                agent=agent_name,
                tick=tick,
                kind="message",
                payload={"text": "benchmark"},
                tags=[]
            )
            write_outbox_entry(base_path, agent_name, entry)

def benchmark():
    base_path = Path("./bench_cleanup_env")
    num_agents = 50
    msgs_per_agent = 100

    setup_benchmark_env(base_path, num_agents, msgs_per_agent)

    print("Starting benchmark...")
    start_time = time.time()

    # Run cleanup 100 times to simulate 100 ticks
    # We use a current_tick that won't delete anything to measure pure scan overhead
    # or one that deletes.
    # Let's measure pure scan overhead first (common case: nothing to delete)
    current_tick = 500 # Messages are at 100 and 1000. Max age 100.
    # 100 is too old (500 - 100 = 400 > 100). Wait.
    # if current_tick - tick_val > max_age_ticks:
    # 500 - 100 = 400. 400 > 100. So tick 100 messages will be deleted.
    # 500 - 1000 = -500. Not deleted.

    # We want to measure SCAN cost, so let's set current_tick such that nothing is deleted.
    # messages at 100, 1000.
    # current_tick = 150. Max age 100.
    # 150 - 100 = 50 < 100. kept.
    # 150 - 1000 = ... kept.

    iterations = 100
    for _ in range(iterations):
        cleanup_old_outbox_entries(base_path, current_tick=150, max_age_ticks=100)

    end_time = time.time()
    duration = end_time - start_time
    print(f"Total time for {iterations} cleanups: {duration:.4f}s")
    print(f"Average time per cleanup: {duration/iterations*1000:.4f}ms")

    # Cleanup
    shutil.rmtree(base_path)

if __name__ == "__main__":
    benchmark()
