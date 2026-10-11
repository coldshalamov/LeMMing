import sys
with open('lemming/memory.py', 'r') as f:
    content = f.read()

content = content.replace("def save_memory(base_path: Path, agent_name: str, key: str, value: Any, operation: str = 'set', tick: int | None = None) -> None:", "def save_memory(\n    base_path: Path, agent_name: str, key: str, value: Any, operation: str = 'set', tick: int | None = None\n) -> None:")

content = content.replace("        entry = {'key': key, 'value': value, 'timestamp': datetime.now(UTC).isoformat(), 'agent': agent_name, 'operation': operation, 'tick': tick}", "        entry = {\n            'key': key,\n            'value': value,\n            'timestamp': datetime.now(UTC).isoformat(),\n            'agent': agent_name,\n            'operation': operation,\n            'tick': tick\n        }")

with open('lemming/memory.py', 'w') as f:
    f.write(content)

with open('tests/test_api_auth.py', 'r') as f:
    content = f.read()

content = content.replace('        data=\'{"name": "test_agent_2", "title": "Test Agent", "model": {"key": "gpt"}, "permissions": {"read_outboxes": [], "tools": []}, "schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, "instructions": "test"}\')', '        data=\'{"name": "test_agent_2", "title": "Test", "model": {"key": "gpt"}, "permissions": {"read_outboxes": [], "tools": []}, "schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, "instructions": "test"}\')')

with open('tests/test_api_auth.py', 'w') as f:
    f.write(content)
