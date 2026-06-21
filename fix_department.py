with open("lemming/department_cli.py", "r") as f:
    content = f.read()

content = content.replace("from .cli import setup_logging\n\n    setup_logging(level=\"INFO\")", "import logging\n    logging.basicConfig(level=logging.INFO)")

with open("lemming/department_cli.py", "w") as f:
    f.write(content)
