# Sentinel's Journal

## 2024-05-22 - Path Traversal via Suffix Collision
**Vulnerability:** Path traversal was possible in `_is_path_allowed` because it used `str(path).startswith(str(parent))` without a trailing separator. This allowed access to sibling directories with names sharing the same prefix (e.g., `workspace` and `workspace_admin`).
**Learning:** `pathlib.Path.resolve()` removes trailing slashes, making naive string prefix checks vulnerable to suffix collisions.
**Prevention:** Use `path.is_relative_to(parent)` (Python 3.9+) or ensure the parent path string ends with the system separator (`os.sep`) before checking prefixes.
