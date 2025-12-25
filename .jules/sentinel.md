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
## 2025-02-14 - API Agent Logs Path Traversal
**Vulnerability:** The `_read_agent_logs` function in `lemming/api.py` constructed file paths using an unvalidated `agent_name` argument (e.g., `base_path / "agents" / agent_name / "logs"`). This allowed directory traversal attacks via the `/api/agents/{agent_name}/logs` endpoint, potentially exposing files outside the agent's directory.
**Learning:** Even internal helper functions called by API endpoints must validate their inputs, especially when dealing with filesystem paths. Manual path construction (`/`) bypasses centralized validation logic.
**Prevention:** Always use centralized path helpers (like `get_logs_dir`) that include validation, or explicitly call validation functions (`validate_agent_name`) before using user input in path operations.
