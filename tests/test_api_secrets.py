
import subprocess
import sys
import json
import os
from pathlib import Path

def test_secrets_shadowing_fix(tmp_path):
    """
    Test that importing lemming.api with a secrets.json file present
    does not cause the 'secrets' module to be shadowed by a local variable.
    """

    # Setup secrets.json
    secrets_file = tmp_path / "secrets.json"
    with open(secrets_file, "w") as f:
        json.dump({"OPENAI_API_KEY": "test-key"}, f)

    # Create a python script that imports api and checks verify_admin_access
    script_content = """
import os
import sys
import asyncio
from unittest.mock import MagicMock

# Set environment variables for lemming base path
os.environ["LEMMING_BASE_PATH"] = sys.argv[1]
# Set admin key to test verification
os.environ["LEMMING_ADMIN_KEY"] = "admin-secret"

try:
    import lemming.api

    # Mock request
    mock_request = MagicMock()
    # The verify_admin_access checks X-Admin-Key header
    mock_request.headers.get.return_value = "admin-secret"

    # Call verify_admin_access
    # This will fail if 'secrets' module is shadowed by local variable
    asyncio.run(lemming.api.verify_admin_access(mock_request))
    print("SUCCESS")
except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
"""
    script_path = tmp_path / "check_script.py"
    with open(script_path, "w") as f:
        f.write(script_content)

    # Run the script using the current python executable
    result = subprocess.run(
        [sys.executable, str(script_path), str(tmp_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        # If it failed, check output for the specific error
        print(f"Script output:\n{result.stdout}\nError:\n{result.stderr}")
        assert result.returncode == 0, f"Script failed: {result.stdout}"

    assert "SUCCESS" in result.stdout
