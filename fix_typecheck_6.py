import re

def add_type_ignore(filepath, search_strings):
    with open(filepath, "r") as f:
        lines = f.readlines()

    with open(filepath, "w") as f:
        for line in lines:
            if any(s in line for s in search_strings):
                if "# type: ignore" not in line:
                    line = line.rstrip() + "  # type: ignore\n"
            f.write(line)

add_type_ignore("lemming/config_validation.py", ["import jsonschema"])
add_type_ignore("lemming/providers.py", ["import openai", "import anthropic"])
add_type_ignore("lemming/api.py", ["from fastapi"])

with open("lemming/config_validation.py", "r") as f:
    c = f.read()
c = c.replace(
    "    return validator.iter_errors(data)",
    "    yield from validator.iter_errors(data)"
)
with open("lemming/config_validation.py", "w") as f:
    f.write(c)
