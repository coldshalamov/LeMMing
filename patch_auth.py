import re

with open("tests/test_api_auth.py", "r") as f:
    content = f.read()

# Fix the long line by splitting the json string nicely
pattern = r'\'{"name": "source".*?"instructions": "test"}\''
replacement = r"""'''{
                "name": "source",
                "title": "Src",
                "short_description": "Src",
                "model": {"key": "gpt"},
                "permissions": {"read_outboxes": [], "tools": []},
                "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},
                "instructions": "test"
            }'''"""
content = re.sub(pattern, replacement, content)

with open("tests/test_api_auth.py", "w") as f:
    f.write(content)
