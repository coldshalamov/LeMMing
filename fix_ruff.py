import subprocess

subprocess.run(["python", "-m", "ruff", "check", "tests/test_tools_security.py", "--fix", "--unsafe-fixes"])
subprocess.run(["python", "-m", "ruff", "format", "tests/test_tools_security.py"])
