import os
from typing import Optional

def get_safe_env(env: Optional[dict[str, str]] = None) -> dict[str, str]:
    """Return a safe copy of the environment variables.

    This prevents leaking sensitive variables (like API keys) to child processes.
    """
    safe_env = os.environ.copy()

    # Remove sensitive keys
    keys_to_remove = []
    for k in safe_env:
        upper_k = k.upper()
        if "API_KEY" in upper_k or "TOKEN" in upper_k or "SECRET" in upper_k:
            keys_to_remove.append(k)

    for k in keys_to_remove:
        del safe_env[k]

    if env:
        safe_env.update(env)

    return safe_env
