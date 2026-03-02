with open("lemming/config_validation.py", "r") as f:
    lines = f.readlines()
with open("lemming/config_validation.py", "w") as f:
    for line in lines:
        if "import jsonschema" in line:
            line = "import jsonschema  # type: ignore\n"
        if "yield from" in line:
            line = "    yield from validator.iter_errors(data)  # type: ignore\n"
        f.write(line)

with open("lemming/providers.py", "r") as f:
    lines = f.readlines()
with open("lemming/providers.py", "w") as f:
    for line in lines:
        if "import openai" in line:
            line = "import openai  # type: ignore\n"
        if "import anthropic" in line:
            line = "import anthropic  # type: ignore\n"
        f.write(line)
