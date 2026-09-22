import time
import shutil
import uuid
import json
from pathlib import Path
from lemming.messages import OutboxEntry, write_outbox_entry, read_multi_agent_outbox_entries
from lemming.paths import get_agents_dir, get_outbox_dir

BASE_PATH = Path("benchmark_env_opt")

def setup_env(num_agents=50, msgs_per_agent=100):
    if BASE_PATH.exists():
        shutil.rmtree(BASE_PATH)
    BASE_PATH.mkdir(parents=True)
    (BASE_PATH / "agents").mkdir()

    agents = [f"agent_{i}" for i in range(num_agents)]

    print(f"Generating {num_agents} agents with {msgs_per_agent} messages each...")

    for agent in agents:
        agent_dir = get_agents_dir(BASE_PATH) / agent
        agent_dir.mkdir()
        (agent_dir / "outbox").mkdir()

        for i in range(msgs_per_agent):
            tick = i + 1
            entry = OutboxEntry.create(
                agent=agent,
                tick=tick,
                kind="message",
                payload={"text": f"Message {i} from {agent} with some payload padding " * 10},
                tags=[],
            )
            write_outbox_entry(BASE_PATH, agent, entry)

    return agents

def benchmark_optimized(agents, limit=50):
    start = time.time()
    result = read_multi_agent_outbox_entries(BASE_PATH, agents, limit=limit)
    duration = time.time() - start
    print(f"Optimized approach: {duration:.4f}s")
    return len(result)

if __name__ == "__main__":
    agents = setup_env(num_agents=50, msgs_per_agent=100)

    print("Benchmarking...")
    count = benchmark_optimized(agents, limit=50)
    print(f"Got {count} messages")

    # Cleanup
    shutil.rmtree(BASE_PATH)
