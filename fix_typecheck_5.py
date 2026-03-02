with open("lemming/department_cli.py", "r") as f:
    c = f.read()
c = c.replace(
    "setup_logging(base_path, level=\"INFO\")",
    "base_path = Path.cwd()\n    setup_logging(base_path, level=\"INFO\")"
)
with open("lemming/department_cli.py", "w") as f:
    f.write(c)
