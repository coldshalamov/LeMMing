import re

# Fix lemming/config_validation.py
with open('lemming/config_validation.py', 'r') as f:
    content = f.read()

content = content.replace('import jsonschema', 'import jsonschema  # type: ignore[import-untyped]')
content = re.sub(
    r'def get_schema_errors\((.*?)\) -> Iterable\[Any\]:\n',
    r'def get_schema_errors(\1) -> Any:\n',
    content
)

with open('lemming/config_validation.py', 'w') as f:
    f.write(content)

# Fix lemming/department_cli.py
with open('lemming/department_cli.py', 'r') as f:
    content = f.read()

content = content.replace('setup_logging(base_path, level="INFO")', 'base_path_obj = Path(base_path)\n    setup_logging(base_path_obj, level="INFO")')

with open('lemming/department_cli.py', 'w') as f:
    f.write(content)
