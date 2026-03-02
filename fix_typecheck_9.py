with open("lemming/api.py", "r") as f:
    lines = f.readlines()
with open("lemming/api.py", "w") as f:
    for line in lines:
        if "from fastapi import Depends" in line:
            if "# type: ignore" not in line:
                line = line.rstrip() + "  # type: ignore\n"
        f.write(line)
