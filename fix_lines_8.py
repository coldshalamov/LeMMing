with open('lemming/config_validation.py', 'r') as f:
    content = f.read()

content = content.replace('from jsonschema import Draft7Validator', 'from jsonschema import Draft7Validator  # type: ignore[import-untyped]')

with open('lemming/config_validation.py', 'w') as f:
    f.write(content)
