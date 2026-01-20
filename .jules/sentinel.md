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
