import os

api_path = "lemming/api.py"
with open(api_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "from .cli import setup_logging" in line:
        pass
with open(api_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

cli_path = "lemming/department_cli.py"
with open(cli_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "from lemming.cli import setup_logging" not in line and "setup_logging" in line:
        lines[i] = line.replace("setup_logging", "# setup_logging")
with open(cli_path, "w", encoding="utf-8") as f:
    f.writelines(lines)
