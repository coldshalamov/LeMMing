tools_path = "lemming/tools.py"
with open(tools_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "base_search = (base_path / \"shared\").resolve()" in line:
        lines[i] = ""
with open(tools_path, "w", encoding="utf-8") as f:
    f.writelines(lines)
