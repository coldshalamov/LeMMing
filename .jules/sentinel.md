## 2024-05-24 - Directory Suffix Vulnerability
**Vulnerability:** The `FileWriteTool` and `CreateAgentTool` used `str(path).startswith(str(base))` for path validation. This allowed path traversal to sibling directories sharing a common prefix (e.g., `workspace_evil` matches `workspace`).
**Learning:** String-based path checks are dangerous because they don't respect path separators.
**Prevention:** Always use `pathlib.Path.is_relative_to()` (Python 3.9+) for path containment checks. It correctly handles path semantics.
