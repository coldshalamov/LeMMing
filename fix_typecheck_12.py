with open("lemming/config_validation.py", "r") as f:
    lines = f.readlines()
with open("lemming/config_validation.py", "w") as f:
    for line in lines:
        if "return validator.iter_errors(instance)" in line:
            line = "    yield from validator.iter_errors(instance)\n"
        f.write(line)
