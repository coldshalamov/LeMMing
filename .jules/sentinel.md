## 2024-02-14 - Overly Permissive CORS Configuration
**Vulnerability:** The FastAPI application in `lemming/api.py` was configured with `allow_origins=["*"]` along with `allow_credentials=True`. This is a dangerous configuration that allows any website to make authenticated requests to the API if the server reflects the origin (which Starlette does in this config) or simply misleads developers into thinking it's safe.
**Learning:** Default templates or quick-start guides often use `allow_origins=["*"]` for convenience, but this should never be used in production, especially with credentials. It defeats the purpose of SOP.
**Prevention:** Use an environment variable (e.g., `ALLOWED_ORIGINS`) to strictly define allowed origins. Default to localhost only for development.
## 2024-10-09 - ShellTool Command Injection
**Vulnerability:** The `ShellTool` used `subprocess.run(shell=True)` which allowed arbitrary command execution and path traversal via chained commands or relative paths (e.g., `cat ../../secret`).
**Learning:** Generic shell tools in AI agent frameworks are extremely dangerous. Even with `cwd` set, `shell=True` allows escaping the directory.
**Prevention:** Always use `shell=False` and pass arguments as a list. Explicitly validate that file paths in arguments do not traverse outside the intended workspace using checks for `..` and absolute paths.
