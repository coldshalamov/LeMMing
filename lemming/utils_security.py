def sanitize_env_for_subprocess(env: dict[str, str]) -> dict[str, str]:
    """
    Sanitizes environment variables to prevent leaking sensitive secrets to untrusted subprocesses.
    Removes common secret keys like API keys, tokens, and passwords.
    """
    sanitized = {}
    for k, v in env.items():
        k_upper = k.upper()
        if any(secret in k_upper for secret in ["API_KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"]):
            continue
        sanitized[k] = v
    return sanitized
