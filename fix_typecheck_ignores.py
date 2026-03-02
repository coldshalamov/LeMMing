with open("lemming/providers.py", "r") as f:
    lines = f.readlines()
with open("lemming/providers.py", "w") as f:
    for line in lines:
        if "from openai import OpenAI" in line:
            line = line.replace("\n", "  # type: ignore\n")
        if "from anthropic import Anthropic" in line:
            line = line.replace("\n", "  # type: ignore\n")
        f.write(line)

with open("lemming/department_cli.py", "r") as f:
    lines = f.readlines()
with open("lemming/department_cli.py", "w") as f:
    for line in lines:
        if "import click" in line:
            line = line.replace("\n", "  # type: ignore\n")
        f.write(line)

with open("lemming/cli.py", "r") as f:
    lines = f.readlines()
with open("lemming/cli.py", "w") as f:
    for line in lines:
        if "import uvicorn" in line:
            line = line.replace("\n", "  # type: ignore\n")
        f.write(line)

with open("lemming/api.py", "r") as f:
    lines = f.readlines()
with open("lemming/api.py", "w") as f:
    for line in lines:
        if "from fastapi.middleware.cors import CORSMiddleware" in line:
            line = line.replace("\n", "  # type: ignore\n")
        if "from pydantic import BaseModel, ConfigDict, Field, field_validator" in line:
            line = line.replace("\n", "  # type: ignore\n")
        f.write(line)
