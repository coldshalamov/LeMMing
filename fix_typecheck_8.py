with open("lemming/config_validation.py", "r") as f:
    c = f.read()
c = c.replace("import jsonschema  # type: ignore", "import jsonschema")
c = c.replace("import jsonschema", "import jsonschema  # type: ignore")

with open("lemming/config_validation.py", "w") as f:
    f.write(c)


with open("lemming/providers.py", "r") as f:
    c = f.read()

c = c.replace("import openai  # type: ignore", "import openai")
c = c.replace("import openai", "import openai  # type: ignore")
c = c.replace("import anthropic  # type: ignore", "import anthropic")
c = c.replace("import anthropic", "import anthropic  # type: ignore")
with open("lemming/providers.py", "w") as f:
    f.write(c)


with open("lemming/api.py", "r") as f:
    lines = f.readlines()

with open("lemming/api.py", "w") as f:
    for line in lines:
        if "from fastapi import" in line:
            line = line.replace("  # type: ignore", "")
        if "from fastapi.middleware.cors import CORSMiddleware" in line:
            if "# type: ignore" not in line:
                line = line.rstrip() + "  # type: ignore\n"
        f.write(line)
