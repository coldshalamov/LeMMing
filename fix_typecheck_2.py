import re

with open("lemming/config_validation.py", "r") as f:
    c = f.read()

c = c.replace(
    "import jsonschema  # type: ignore",
    "import jsonschema"
)

with open("lemming/config_validation.py", "w") as f:
    f.write(c)


with open("lemming/providers.py", "r") as f:
    c = f.read()

c = c.replace(
    "import openai  # type: ignore",
    "import openai"
)
c = c.replace(
    "import anthropic  # type: ignore",
    "import anthropic"
)

with open("lemming/providers.py", "w") as f:
    f.write(c)

with open("lemming/api.py", "r") as f:
    c = f.read()

c = c.replace(
    "from fastapi import Depends, FastAPI, HTTPException, Request, status as http_status, WebSocket, WebSocketDisconnect",
    "from fastapi import Depends, FastAPI, HTTPException, Request, status as http_status, WebSocket, WebSocketDisconnect  # type: ignore"
)
c = c.replace(
    "from fastapi.middleware.cors import CORSMiddleware",
    "from fastapi.middleware.cors import CORSMiddleware  # type: ignore"
)
c = c.replace(
    "from pydantic import BaseModel, ConfigDict, Field, field_validator",
    "from pydantic import BaseModel, ConfigDict, Field, field_validator  # type: ignore"
)

with open("lemming/api.py", "w") as f:
    f.write(c)

with open("lemming/department_cli.py", "r") as f:
    c = f.read()
c = c.replace("from .cli import get_config_dir", "from .cli import get_config_dir, setup_logging")
c = c.replace("setup_logging(base_path, args.debug)", "setup_logging(args.debug)")
with open("lemming/department_cli.py", "w") as f:
    f.write(c)
