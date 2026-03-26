import re

# Fix lemming/config_validation.py
with open('lemming/config_validation.py', 'r') as f:
    content = f.read()

content = content.replace('import jsonschema', 'import jsonschema  # type: ignore[import-untyped]')
content = re.sub(
    r'def get_schema_errors\((.*?)\) -> Iterable\[Any\]:',
    r'def get_schema_errors(\1) -> Any:',
    content
)

with open('lemming/config_validation.py', 'w') as f:
    f.write(content)

# Fix lemming/department_cli.py
with open('lemming/department_cli.py', 'r') as f:
    content = f.read()

content = content.replace('base_path_obj = Path(base_path)\n    setup_logging(base_path_obj, level="INFO")', 'setup_logging(Path.cwd(), level="INFO")')

with open('lemming/department_cli.py', 'w') as f:
    f.write(content)
