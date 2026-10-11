with open('tests/test_api_auth.py', 'r') as f:
    content = f.read()

content = content.replace('''    response = client.post(
        "/api/agents",
        data='{"name": "test_agent_2", "title": "Test", "model": {"key": "gpt"}, "permissions": {"read_outboxes": [], "tools": []}, "schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, "instructions": "test"}',
        headers={"Authorization": "Bearer admin_secret"},
    )''', '''    response = client.post(
        "/api/agents",
        data='{"name": "test_agent_2", "title": "Test", "model": {"key": "gpt"}, '
        '"permissions": {"read_outboxes": [], "tools": []}, "schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, '
        '"instructions": "test"}',
        headers={"Authorization": "Bearer admin_secret"},
    )''')
with open('tests/test_api_auth.py', 'w') as f:
    f.write(content)
