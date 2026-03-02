import os

with open("lemming/config_validation.py", "r") as f:
    c = f.read()

c = c.replace(
    "import jsonschema  # type: ignore  # type: ignore",
    "import jsonschema  # type: ignore"
)
c = c.replace(
    "import jsonschema",
    "import jsonschema  # type: ignore"
)
c = c.replace(
    "import jsonschema  # type: ignore  # type: ignore",
    "import jsonschema  # type: ignore"
)

with open("lemming/config_validation.py", "w") as f:
    f.write(c)

with open("lemming/providers.py", "r") as f:
    c = f.read()
c = c.replace(
    "import openai  # type: ignore  # type: ignore",
    "import openai  # type: ignore"
)
c = c.replace(
    "import openai",
    "import openai  # type: ignore"
)
c = c.replace(
    "import anthropic  # type: ignore  # type: ignore",
    "import anthropic  # type: ignore"
)
c = c.replace(
    "import anthropic",
    "import anthropic  # type: ignore"
)
with open("lemming/providers.py", "w") as f:
    f.write(c)


with open("lemming/api.py", "r") as f:
    lines = f.readlines()

with open("lemming/api.py", "w") as f:
    for i, line in enumerate(lines):
        if "from fastapi.middleware.cors" in line and "type: ignore" in line:
            line = line.replace("  # type: ignore", "")
        f.write(line)
