import os

with open('lemming/config_validation.py', 'r') as f:
    content = f.read()
content = content.replace('import jsonschema', 'import jsonschema  # type: ignore[import-untyped]')
content = content.replace(
    'def get_schema_errors(data: Any, schema_name: str) -> Iterable[Any]:',
    'def get_schema_errors(data: Any, schema_name: str) -> "Iterable[Any]":\n    # Use quotes around Iterable[Any] due to mypy finding the return type Any'
)
# Actually the Any return can be fixed by typing it correctly
content = content.replace('return validator.iter_errors(data)', 'return validator.iter_errors(data)  # type: ignore')
with open('lemming/config_validation.py', 'w') as f:
    f.write(content)


with open('lemming/providers.py', 'r') as f:
    content = f.read()
content = content.replace('import requests', 'import requests  # type: ignore[import-untyped]')
with open('lemming/providers.py', 'w') as f:
    f.write(content)


with open('lemming/api.py', 'r') as f:
    content = f.read()
content = content.replace('for k, v in secrets.items():', 'for k, v in secrets_data.items():')
content = content.replace('secrets = json.load(f)', 'secrets_data = json.load(f)')
content = content.replace('if secrets and isinstance(secrets, dict):', 'if secrets_data and isinstance(secrets_data, dict):')
content = content.replace('secrets: dict[str, Any] = {}', 'secrets_data: dict[str, Any] = {}')
with open('lemming/api.py', 'w') as f:
    f.write(content)


with open('lemming/department_cli.py', 'r') as f:
    content = f.read()
content = content.replace('from .cli import setup_logging', 'from .logging_config import setup_logging')
content = content.replace('setup_logging(level="INFO")', 'setup_logging(base_path, level="INFO")')
with open('lemming/department_cli.py', 'w') as f:
    f.write(content)
