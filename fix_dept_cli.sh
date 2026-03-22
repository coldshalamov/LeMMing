sed -i 's/from .cli import setup_logging/from .logging_config import setup_logging/g' lemming/department_cli.py
sed -i 's/setup_logging(level="INFO")/setup_logging(Path("."), level="INFO")/g' lemming/department_cli.py
