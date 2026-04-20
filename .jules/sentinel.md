## 2024-05-23 - Prevent DoS via Unbounded File Reads
**Vulnerability:** `FileReadTool` read entire files into memory without size limits, allowing malicious agents or large log files to trigger OOM crashes.
**Learning:** `pathlib.Path.read_text()` is convenient but dangerous for untrusted input sizes. Always check `stat().st_size` first.
**Prevention:** Enforced 5MB limit on `FileReadTool` and added regression tests to verify rejection of large files.
