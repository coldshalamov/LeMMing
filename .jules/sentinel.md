## 2024-02-14 - Overly Permissive CORS Configuration
**Vulnerability:** The FastAPI application in `lemming/api.py` was configured with `allow_origins=["*"]` along with `allow_credentials=True`. This is a dangerous configuration that allows any website to make authenticated requests to the API if the server reflects the origin (which Starlette does in this config) or simply misleads developers into thinking it's safe.
**Learning:** Default templates or quick-start guides often use `allow_origins=["*"]` for convenience, but this should never be used in production, especially with credentials. It defeats the purpose of SOP.
**Prevention:** Use an environment variable (e.g., `ALLOWED_ORIGINS`) to strictly define allowed origins. Default to localhost only for development.
## 2024-10-09 - ShellTool Command Injection
**Vulnerability:** The `ShellTool` used `subprocess.run(shell=True)` which allowed arbitrary command execution and path traversal via chained commands or relative paths (e.g., `cat ../../secret`).
**Learning:** Generic shell tools in AI agent frameworks are extremely dangerous. Even with `cwd` set, `shell=True` allows escaping the directory.
**Prevention:** Always use `shell=False` and pass arguments as a list. Explicitly validate that file paths in arguments do not traverse outside the intended workspace using checks for `..` and absolute paths.
## 2025-02-14 - CreateAgentTool Path Traversal
**Vulnerability:** The `CreateAgentTool` accepted an arbitrary `agent_name` which was used to construct a directory path without validation. This allowed an attacker (via the 'hr' agent) to create directories outside the intended `agents/` folder using path traversal (e.g., `../evil`).
**Learning:** Tool arguments that are used to construct file paths must be rigorously validated. Relying on "it's just a name" is insufficient when that name becomes part of a filesystem path.
**Prevention:** Import and use the strict `validate_agent_name` function from `lemming.paths` in `CreateAgentTool` (and any other tool creating/accessing agent directories) to enforce alphanumeric-only names.
## 2024-05-23 - Path Traversal in Agent Names
**Vulnerability:** The application constructs file paths by directly joining user-provided agent names with base paths. This allows path traversal attacks (e.g., `../etc/passwd`) via the API or other inputs.
**Learning:** `pathlib.Path` joining operations do not automatically sanitize or prevent traversal sequences like `..`. Simply using `path / ".." / "target"` results in a path pointing to `target` outside the intended directory.
**Prevention:** Always validate user-provided path components before using them in filesystem operations. Use a strict allowlist regex (e.g., `^[a-zA-Z0-9_-]+$`) and explicitly reject `.` and `..` to ensure the resulting path stays within the intended directory.
