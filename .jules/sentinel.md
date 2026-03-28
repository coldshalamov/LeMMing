## 2024-05-24 - Directory Suffix Vulnerability
**Vulnerability:** The `FileWriteTool` and `CreateAgentTool` used `str(path).startswith(str(base))` for path validation. This allowed path traversal to sibling directories sharing a common prefix (e.g., `workspace_evil` matches `workspace`).
**Learning:** String-based path checks are dangerous because they don't respect path separators.
**Prevention:** Always use `pathlib.Path.is_relative_to()` (Python 3.9+) for path containment checks. It correctly handles path semantics.

## 2024-05-25 - Missing Rate Limiting on Sensitive Endpoints
**Vulnerability:** The `update_engine_config` and `trigger_tick` endpoints lacked rate limiting, allowing potential DoS or brute-force attacks on engine configuration and execution.
**Learning:** Developers often secure "creation" endpoints (like `create_agent`) but forget operational/configuration endpoints.
**Prevention:** Apply rate limiting middleware/dependencies to ALL state-mutating endpoints, especially those controlling system-wide configuration or resource-intensive operations.

## 2024-05-26 - Optional Authentication for Local/Cloud Hybrid Apps
**Vulnerability:** Sensitive endpoints (`/api/engine/config`) were unauthenticated by default, which is acceptable for local single-user apps but critical for cloud deployments.
**Learning:** Enforcing auth by default breaks local Dev experience. "Opt-in" security via environment variables (`LEMMING_ADMIN_KEY`) bridges this gap.
**Prevention:** Implement an auth dependency that checks for an env var. If set, require a header. If not, allow access. Always use `secrets.compare_digest` for key comparison.

## 2024-05-27 - Workspace Hijacking via Name Collision
**Vulnerability:** Tools relied on `agent_name` to resolve `agent_path`. Nested agents (e.g., `agents/sub/victim`) could spoof root agents (e.g., `agents/victim`) because names are not unique across the tree.
**Learning:** In a hierarchical or nested system, "name" is often ambiguous. Path resolution must be context-aware (pass the instance's path) rather than derived from a non-unique identifier.
**Prevention:** Pass the authoritative `agent_path` (or unique ID) from the engine execution context to tools, rather than re-resolving it from the name.

## 2024-05-28 - Argument Injection in CLI Wrappers
**Vulnerability:** The `CLIProvider` wrapped local CLI tools and passed user input directly as arguments. This allowed users to inject flags (e.g., `-n`, `-r`) into tools, potentially altering their behavior or executing unsafe operations.
**Learning:** Even when using `subprocess.run(shell=False)`, Argument Injection is possible if untrusted input starts with `-` and the tool interprets it as a flag.
**Prevention:** Sanitize inputs to CLI wrappers by blocking leading dashes or using the `--` delimiter if supported by the tool.

## 2024-05-29 - WebSocket Auth Bypass with HTTP Dependencies
**Vulnerability:** The `/ws` endpoint used standard HTTP dependencies. While FastAPI supports `Depends` on WebSockets, standard `HTTPException(401)` does not close the WebSocket connection with a policy violation code (1008), leaving the connection open in some cases or failing silently without proper protocol closure.
**Learning:** WebSocket auth requires different exception handling than HTTP. Standard HTTP auth dependencies are not drop-in replacements for WebSocket security.
**Prevention:** Create dedicated `verify_websocket_access` dependencies that raise `WebSocketException(code=status.WS_1008_POLICY_VIOLATION)` on failure.

## 2024-05-30 - WebSocket Auth and Linting
**Vulnerability:** The `/ws` endpoint was secured, but the CI pipeline failed due to linting errors (unused variables, line lengths) introduced or revealed by the changes.
**Learning:** Security fixes must also adhere to strict code style guidelines enforced by CI. `ruff` and `black` checks are mandatory.
**Prevention:** Always run `make lint-fix` and `make format` before submitting, and manually verify that auto-fixes don't introduce new issues or leave residual style violations (like long strings).

## 2024-05-31 - Black vs Ruff Formatting
**Vulnerability:** CI failed due to conflicting formatting. Ruff fixes (like import sorting) and manual fixes for lint errors (like line lengths) can leave code in a state that Black considers unformatted.
**Learning:** Manual edits to fix lint errors must always be followed by `make format` (Black) to ensure style consistency. Relying on `ruff check --fix` alone is insufficient if the project enforces Black.
**Prevention:** In the pre-commit workflow, always run `make format` *after* any code changes, including those from `ruff --fix`.

## 2024-06-01 - Type Stubs and Shadowing
**Vulnerability:** CI failed due to missing type stubs (`jsonschema`, `requests`) and variable shadowing (`secrets` local var vs module).
**Learning:** Type checking (mypy) catches subtle issues like shadowing standard library modules. Always rename local variables if they conflict with imports. Install or ignore missing stubs explicitly.
**Prevention:** Run `mypy` locally before submitting. When using `secrets` module, avoid naming variables `secrets`.
