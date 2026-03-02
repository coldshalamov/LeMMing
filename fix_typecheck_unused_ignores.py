with open("lemming/providers.py", "r") as f:
    lines = f.readlines()
with open("lemming/providers.py", "w") as f:
    for line in lines:
        if "from openai import OpenAI  # type: ignore" in line:
            line = line.replace("  # type: ignore", "")
        if "from anthropic import Anthropic  # type: ignore" in line:
            line = line.replace("  # type: ignore", "")
        f.write(line)

with open("lemming/department_cli.py", "r") as f:
    lines = f.readlines()
with open("lemming/department_cli.py", "w") as f:
    for line in lines:
        if "import click  # type: ignore" in line:
            line = line.replace("  # type: ignore", "")
        f.write(line)

with open("lemming/cli.py", "r") as f:
    lines = f.readlines()
with open("lemming/cli.py", "w") as f:
    for line in lines:
        if "import uvicorn  # type: ignore" in line:
            line = line.replace("  # type: ignore", "")
        f.write(line)

with open("lemming/api.py", "r") as f:
    lines = f.readlines()
with open("lemming/api.py", "w") as f:
    for line in lines:
        if "from fastapi import Depends, FastAPI, HTTPException, Request, status as http_status, WebSocket, WebSocketDisconnect  # type: ignore" in line:
            line = line.replace("  # type: ignore", "")
        if "from fastapi.middleware.cors import CORSMiddleware  # type: ignore" in line:
            line = line.replace("  # type: ignore", "")
        if "from pydantic import BaseModel, ConfigDict, Field, field_validator  # type: ignore" in line:
            line = line.replace("  # type: ignore", "")
        f.write(line)
