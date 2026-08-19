import pytest
import os
from lemming.providers import CLIProvider

from unittest.mock import patch

def test_cli_provider_env_sanitization():
    # Setup malicious env using patch.dict to avoid polluting global state
    with patch.dict(os.environ, {"API_KEY": "secret123", "SUPER_SECRET_TOKEN": "token456"}):
        provider = CLIProvider(command=["env"])

        # Run provider with empty content so 'env' runs without arguments and dumps the environment
        output = provider.call(model_name="test", messages=[{"role": "user", "content": ""}])

        assert "API_KEY" not in output
        assert "SUPER_SECRET_TOKEN" not in output
