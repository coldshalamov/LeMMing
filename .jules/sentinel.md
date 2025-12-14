## 2024-05-23 - Path Traversal in Agent Names
**Vulnerability:** The application constructs file paths by directly joining user-provided agent names with base paths. This allows path traversal attacks (e.g., `../etc/passwd`) via the API or other inputs.
**Learning:** `pathlib.Path` joining operations do not automatically sanitize or prevent traversal sequences like `..`. Simply using `path / ".." / "target"` results in a path pointing to `target` outside the intended directory.
**Prevention:** Always validate user-provided path components before using them in filesystem operations. Use a strict allowlist regex (e.g., `^[a-zA-Z0-9_-]+$`) and explicitly reject `.` and `..` to ensure the resulting path stays within the intended directory.
