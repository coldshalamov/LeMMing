with open("lemming/config_validation.py", "r") as f:
    lines = f.readlines()
with open("lemming/config_validation.py", "w") as f:
    for line in lines:
        if "from jsonschema import" in line:
            line = "from jsonschema import Draft7Validator  # type: ignore\n"
        f.write(line)

with open("lemming/providers.py", "r") as f:
    lines = f.readlines()
with open("lemming/providers.py", "w") as f:
    for line in lines:
        if "from openai import" in line:
            line = "            from openai import OpenAI  # type: ignore\n"
        if "from anthropic import" in line:
            line = "            from anthropic import Anthropic  # type: ignore\n"
        f.write(line)
