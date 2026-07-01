import time
from pathlib import Path
from lemming.config_validation import _iter_schema_errors

def run_benchmark():
    data = {
        "base_turn_seconds": 5,
        "summary_every_n_turns": 10,
        "max_turns": None,
        "max_outbox_age_ticks": 100,
    }
    start_time = time.time()
    for _ in range(1000):
        list(_iter_schema_errors("org_config_schema.json", data))
    end_time = time.time()
    print(f"Elapsed time for 1000 runs of _iter_schema_errors: {end_time - start_time:.4f} seconds")

if __name__ == '__main__':
    run_benchmark()
