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
## 2024-04-26 - [Fix secrets shadow causing Admin Auth Bypass]
**Vulnerability:** A local variable named `secrets` shadowed the imported standard library `secrets` module, causing `secrets.compare_digest()` to raise an AttributeError. Since it threw a 500 error, authorization essentially failed closed, but it's a critical code logic bug preventing correct admin token checks.
**Learning:** Be careful when naming variables containing secret values that they don't shadow the widely used `import secrets` Python module.
**Prevention:** Use a different variable name such as `loaded_secrets` for JSON dictionary containing secrets, and use type linters that can catch shadowings if configured.
