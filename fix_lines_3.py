with open('tests/test_api_auth.py', 'r') as f:
    content = f.read()

content = content.replace(
    '            \'{"name": "source", "title": "Src", "short_description": "Src", "model": {"key": "gpt"}, "permissions": {"read_outboxes": [], "tools": []}, "schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, "instructions": "test"}\'',
    '            \'{"name": "source", "title": "Src", "short_description": "Src", "model": {"key": "gpt"}, \' \\\n            \'"permissions": {"read_outboxes": [], "tools": []}, "schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, \' \\\n            \'"instructions": "test"}\''
)

with open('tests/test_api_auth.py', 'w') as f:
    f.write(content)
