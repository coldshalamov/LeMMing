with open("lemming/memory.py", "r") as f:
    c = f.read()
c = c.replace(
    "def save_memory(base_path: Path, agent_name: str, key: str, value: Any, operation: str = 'set', tick: int | None = None) -> None:",
    "def save_memory(\n    base_path: Path,\n    agent_name: str,\n    key: str,\n    value: Any,\n    operation: str = 'set',\n    tick: int | None = None\n) -> None:"
)
c = c.replace(
    "        entry = {'timestamp': datetime.now(UTC).isoformat(), 'agent': agent_name, 'operation': operation, 'tick': tick}",
    "        entry = {\n            'timestamp': datetime.now(UTC).isoformat(),\n            'agent': agent_name,\n            'operation': operation,\n            'tick': tick\n        }"
)
with open("lemming/memory.py", "w") as f:
    f.write(c)

with open("lemming/providers.py", "r") as f:
    c = f.read()
c = c.replace(
    "    def __init__(self, command: str | list[str], id: str | None = None, api_key: str | None = None, config: dict[str, str] | None = None, timeout: float = 60.0, prevent_arg_injection: bool = True):",
    "    def __init__(\n        self,\n        command: str | list[str],\n        id: str | None = None,\n        api_key: str | None = None,\n        config: dict[str, str] | None = None,\n        timeout: float = 60.0,\n        prevent_arg_injection: bool = True,\n    ):"
)
c = c.replace(
    "            raise ValueError(f\"Security violation: Prompt '{prompt}' starts with '-' which could be interpreted as a flag. \"\n                             \"Disable 'prevent_arg_injection' in provider config if this is intended.\")",
    "            raise ValueError(\n                f\"Security violation: Prompt '{prompt}' starts with '-' which \"\n                \"could be interpreted as a flag. Disable 'prevent_arg_injection' \"\n                \"in provider config if this is intended.\"\n            )"
)
with open("lemming/providers.py", "w") as f:
    f.write(c)

with open("lemming/tools.py", "r") as f:
    c = f.read()
c = c.replace(
    "        if not (target_path.is_relative_to(workspace_dir.resolve()) or target_path.is_relative_to((base_path / \"shared\").resolve())):\n             return ToolResult(False, \"\", \"Security violation: path is outside allowed directories\")",
    "        is_in_workspace = target_path.is_relative_to(workspace_dir.resolve())\n        is_in_shared = target_path.is_relative_to((base_path / \"shared\").resolve())\n        if not (is_in_workspace or is_in_shared):\n            return ToolResult(False, \"\", \"Security violation: path is outside allowed directories\")"
)
with open("lemming/tools.py", "w") as f:
    f.write(c)

with open("tests/test_api_auth.py", "r") as f:
    c = f.read()
c = c.replace(
    "'{\"name\": \"test_agent\", \"title\": \"Test\", \"short_description\": \"test\", \"model\": {\"key\": \"gpt\"}, \"permissions\": {\"read_outboxes\": [], \"tools\": []}, \"schedule\": {\"run_every_n_ticks\": 1, \"phase_offset\": 0}, \"instructions\": \"test\"}'",
    "'{\"name\": \"test_agent\", \"title\": \"Test\", \"short_description\": \"test\", \"model\": {\"key\": \"gpt\"}, \"permissions\": {\"read_outboxes\": [], \"tools\": []}, \"schedule\": {\"run_every_n_ticks\": 1, \"phase_offset\": 0}, \"instructions\": \"t\"}'"
)
with open("tests/test_api_auth.py", "w") as f:
    f.write(c)

with open("tests/test_tools_security.py", "r") as f:
    c = f.read()
c = c.replace(
    "@pytest.mark.skipif(os.name == 'nt', reason=\"ShellTool uses Unix-style tools/commands not available as executables on Windows (e.g. echo)\")",
    "@pytest.mark.skipif(\n    os.name == 'nt',\n    reason=\"ShellTool uses Unix-style tools/commands not available as executables on Windows (e.g. echo)\"\n)"
)
lines = c.split('\n')
new_lines = []
for line in lines:
    if line.strip() == "import os" or line.strip() == "import pytest":
        continue
    new_lines.append(line)
with open("tests/test_tools_security.py", "w") as f:
    f.write("import os\nimport pytest\n" + "\n".join(new_lines))
