with open("lemming/api.py", "r") as f:
    content = f.read()
content = content.replace("secrets = json.load(f)\n            for k, v in secrets.items():", "secrets_data = json.load(f)\n            for k, v in secrets_data.items():")
with open("lemming/api.py", "w") as f:
    f.write(content)
