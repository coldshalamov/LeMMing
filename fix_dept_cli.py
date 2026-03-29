import re

with open("lemming/department_cli.py") as f:
    code = f.read()

code = code.replace("from .cli import setup_logging", "from .logging_config import setup_logging")

# We want to replace:
#     setup_logging(level="INFO")
#
#     base_path = Path.cwd()
#
# with:
#     base_path = Path.cwd()
#     setup_logging(base_path, level="INFO")

code = re.sub(
    r'    setup_logging\(level="INFO"\)\n\n    base_path = Path\.cwd\(\)',
    r'    base_path = Path.cwd()\n    setup_logging(base_path, level="INFO")',
    code
)

with open("lemming/department_cli.py", "w") as f:
    f.write(code)
