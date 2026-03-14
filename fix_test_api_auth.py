with open("tests/test_api_auth.py", "r") as f:
    content = f.read()

import re

# Fix the first long line
old_line1 = '        json={"name": "test_unit", "title": "test", "description": "test", "model": {"key": "gpt"}, "permissions": {"read_outboxes": [], "tools": []}, "schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, "instructions": "test"}'
new_line1 = '        json={\n            "name": "test_unit",\n            "title": "test",\n            "description": "test",\n            "model": {"key": "gpt"},\n            "permissions": {"read_outboxes": [], "tools": []},\n            "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},\n            "instructions": "test"\n        }'
content = content.replace(old_line1, new_line1)

# Fix the second long line
old_line2 = '        (source_dir / "resume.json").write_text(\'{"name": "source", "title": "Src", "short_description": "Src", "model": {"key": "gpt"}, "permissions": {"read_outboxes": [], "tools": []}, "schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, "instructions": "test"}\')'
new_line2 = '        (source_dir / "resume.json").write_text(\n            \'{"name": "source", "title": "Src", "short_description": "Src", \' + \n            \'"model": {"key": "gpt"}, "permissions": {"read_outboxes": [], "tools": []}, \' + \n            \'"schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, "instructions": "test"}\'\n        )'
content = content.replace(old_line2, new_line2)

with open("tests/test_api_auth.py", "w") as f:
    f.write(content)
