sed -i 's/secrets = json.load(f)/secrets_data = json.load(f)/g' lemming/api.py
sed -i 's/for k, v in secrets.items():/for k, v in secrets_data.items():/g' lemming/api.py
