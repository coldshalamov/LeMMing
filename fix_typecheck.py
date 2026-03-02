import re

with open("lemming/config_validation.py", "r") as f:
    c = f.read()

c = c.replace(
    "import jsonschema",
    "import jsonschema  # type: ignore"
)
c = c.replace(
    "    return validator.iter_errors(data)",
    "    yield from validator.iter_errors(data)"
)

with open("lemming/config_validation.py", "w") as f:
    f.write(c)

with open("lemming/providers.py", "r") as f:
    c = f.read()

c = c.replace(
    "import requests",
    "import requests  # type: ignore"
)
c = c.replace(
    "import openai",
    "import openai  # type: ignore"
)
c = c.replace(
    "import anthropic",
    "import anthropic  # type: ignore"
)

with open("lemming/providers.py", "w") as f:
    f.write(c)

with open("lemming/cli.py", "r") as f:
    c = f.read()
c = c.replace(
    "import uvicorn",
    "import uvicorn  # type: ignore"
)
with open("lemming/cli.py", "w") as f:
    f.write(c)

with open("lemming/department_cli.py", "r") as f:
    c = f.read()

c = c.replace(
    "import click",
    "import click  # type: ignore"
)
c = c.replace(
    "from .cli import get_config_dir, setup_logging",
    "from .cli import get_config_dir\nfrom .logging_config import setup_logging"
)
c = c.replace(
    "setup_logging(args.debug)",
    "setup_logging(base_path, args.debug)"
)

with open("lemming/department_cli.py", "w") as f:
    f.write(c)

with open("lemming/api.py", "r") as f:
    c = f.read()

c = c.replace(
    "import secrets",
    "import secrets as secrets_module"
)
c = c.replace(
    "secrets.compare_digest",
    "secrets_module.compare_digest"
)
c = c.replace(
    "    secrets = load_secrets()",
    "    secrets_data = load_secrets()"
)
c = c.replace(
    "    if not secrets or \"api_key\" not in secrets:",
    "    if not secrets_data or \"api_key\" not in secrets_data:"
)
c = c.replace(
    "secrets[\"api_key\"]",
    "secrets_data[\"api_key\"]"
)
c = c.replace(
    "for key, item in secrets.items():",
    "for key, item in secrets_data.items():"
)

with open("lemming/api.py", "w") as f:
    f.write(c)
