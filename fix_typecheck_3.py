with open("lemming/config_validation.py", "r") as f:
    c = f.read()
c = c.replace("import jsonschema", "import jsonschema  # type: ignore")
with open("lemming/config_validation.py", "w") as f:
    f.write(c)

with open("lemming/providers.py", "r") as f:
    c = f.read()
c = c.replace("import openai", "import openai  # type: ignore")
c = c.replace("import anthropic", "import anthropic  # type: ignore")
with open("lemming/providers.py", "w") as f:
    f.write(c)

with open("lemming/api.py", "r") as f:
    c = f.read()
c = c.replace(
    "from fastapi import Depends, FastAPI, HTTPException, Request, status as http_status, WebSocket, WebSocketDisconnect",
    "from fastapi import Depends, FastAPI, HTTPException, Request, status as http_status, WebSocket, WebSocketDisconnect  # type: ignore"
)
with open("lemming/api.py", "w") as f:
    f.write(c)

with open("lemming/department_cli.py", "r") as f:
    c = f.read()
c = c.replace(
    "from .cli import get_config_dir, setup_logging",
    "from .cli import get_config_dir\nfrom .logging_config import setup_logging"
)
c = c.replace("setup_logging(args.debug)", "setup_logging(base_path, args.debug)")
with open("lemming/department_cli.py", "w") as f:
    f.write(c)
