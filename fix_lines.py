import re

# Fix lemming/providers.py
with open('lemming/providers.py', 'r') as f:
    content = f.read()

content = content.replace(
    '        env: dict[str, str] | None = None, timeout: float = 60.0, prevent_arg_injection: bool = True):',
    '        env: dict[str, str] | None = None,\n        timeout: float = 60.0,\n        prevent_arg_injection: bool = True\n    ):'
)
content = content.replace(
    '            raise ValueError(f"Security violation: Prompt \'{prompt}\' starts with \'-\' which could be interpreted as a flag. "\n                             "Disable \'prevent_arg_injection\' in provider config if this is intended.")',
    '            raise ValueError(\n                f"Security violation: Prompt \'{prompt}\' starts with \'-\' "\n                "which could be interpreted as a flag. "\n                "Disable \'prevent_arg_injection\' in provider config if this is intended."\n            )'
)

with open('lemming/providers.py', 'w') as f:
    f.write(content)

# Fix lemming/tools.py
with open('lemming/tools.py', 'r') as f:
    content = f.read()

content = content.replace(
    '        if not (target_path.is_relative_to(workspace_dir.resolve()) or target_path.is_relative_to((base_path / "shared").resolve())):',
    '        in_workspace = target_path.is_relative_to(workspace_dir.resolve())\n        in_shared = target_path.is_relative_to((base_path / "shared").resolve())\n        if not (in_workspace or in_shared):'
)

with open('lemming/tools.py', 'w') as f:
    f.write(content)

# Fix tests/test_api_auth.py
with open('tests/test_api_auth.py', 'r') as f:
    content = f.read()

content = content.replace(
    '\'{"name": "test", "title": "Test", "model": {"key": "gpt"}, "permissions": {"read_outboxes": [], "tools": []}, "schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, "instructions": "test"}\'',
    '\'{"name": "test", "title": "Test", "model": {"key": "gpt"}, \' \\\n                                \'"permissions": {"read_outboxes": [], "tools": []}, \' \\\n                                \'"schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, \' \\\n                                \'"instructions": "test"}\''
)

with open('tests/test_api_auth.py', 'w') as f:
    f.write(content)

# Fix tests/test_tools_security.py
with open('tests/test_tools_security.py', 'r') as f:
    content = f.read()

# Remove imports from middle of file
content = content.replace('import os\n\nimport pytest\n', '')
content = content.replace('import os\nimport pytest\n', '')

# add imports at top
lines = content.split('\n')
if 'import os' not in [line.strip() for line in lines[:20]]:
    lines.insert(0, 'import os')
    lines.insert(1, 'import pytest')

content = '\n'.join(lines)

# Fix line length
content = content.replace(
    '@pytest.mark.skipif(os.name == \'nt\', reason="ShellTool uses Unix-style tools/commands not available as executables on Windows (e.g. echo)")',
    '@pytest.mark.skipif(\n    os.name == \'nt\',\n    reason="ShellTool uses Unix-style tools/commands not available on Windows (e.g. echo)"\n)'
)

with open('tests/test_tools_security.py', 'w') as f:
    f.write(content)
