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

## 2024-05-29 - Scoped Rate Limiting and Variable Shadowing
**Vulnerability:**
1. Rate limits were shared across all endpoints for a given client IP because the in-memory limiter used `client_ip` as the only key. This allowed a Denial of Service (DoS) where consuming quota on a low-priority endpoint (e.g., messaging) blocked high-priority admin endpoints.
2. The `secrets` variable in `lemming/api.py` shadowed the standard library `secrets` module when a secrets file was loaded. This caused 500 errors (`AttributeError`) when attempting to use `secrets.compare_digest` for authentication.
**Learning:**
1. Rate limiters must define scope/buckets. A global "requests per IP" bucket is rarely sufficient for APIs with diverse endpoint costs/priorities.
2. Variable naming matters. Shadowing standard library modules leads to obscure runtime errors that only manifest under specific conditions.
**Prevention:**
1. Always include a "scope" or "action" identifier in rate limit keys (e.g., `ip:action`).
2. Use linters that detect module shadowing, or stick to specific naming conventions for configuration data (e.g., `secrets_config`).
