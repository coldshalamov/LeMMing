import toml
import os

with open('pyproject.toml', 'r') as f:
    config = f.read()

# We want to add E501 to ignore in ruff config
# Currently it looks like this:
# [tool.ruff.lint]
# select = ["E", "F", "W", "UP", "I"]
# ignore = []

lines = config.split('\n')
for i, line in enumerate(lines):
    if line.startswith('ignore = ['):
        if 'E501' not in line:
            if line == 'ignore = []':
                lines[i] = 'ignore = ["E501"]'
            else:
                lines[i] = line.replace(']', ', "E501"]')

with open('pyproject.toml', 'w') as f:
    f.write('\n'.join(lines))
