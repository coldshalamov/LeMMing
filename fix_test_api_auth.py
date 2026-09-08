text = """
            '{"name": "source", "title": "Src", "short_description": "Src", "model": {"key": "gpt"}, ' \\
            '"permissions": {"read_outboxes": [], "tools": []}, ' \\
            '"schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, "instructions": "test"}'
"""
with open("tests/test_api_auth.py") as f:
    content = f.read()

import re
content = re.sub(r'\'\{"name": "source".*"test"\'', text.strip(), content)

with open("tests/test_api_auth.py", "w") as f:
    f.write(content)
