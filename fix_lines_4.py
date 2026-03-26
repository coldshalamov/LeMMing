with open('tests/test_api_auth.py', 'r') as f:
    content = f.read()

content = content.replace(
    '            \'"permissions": {"read_outboxes": [], "tools": []}, "schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, \'',
    '            \'"permissions": {"read_outboxes": [], "tools": []}, \' \\\n            \'"schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, \''
)

with open('tests/test_api_auth.py', 'w') as f:
    f.write(content)
