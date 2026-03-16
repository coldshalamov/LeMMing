# Bolt's Journal

## 2024-05-22 - [Project Structure]
**Learning:** This project uses a file-based architecture for agent communication and state persistence.
**Action:** Focus backend optimizations on file I/O operations (e.g., `os.scandir` instead of `os.listdir` or reading files) and efficient JSON handling.

## 2024-05-23 - [EAFP for File I/O]
**Learning:** `Path.exists()` incurs an extra syscall. In this file-heavy architecture, using EAFP (try/except FileNotFoundError) for `load_memory` and `delete_memory` saves significant overhead. For `save_memory`, optimistic writing (assuming directory exists) with a fallback to `mkdir` handles the common case (updates) efficiently.
**Action:** Apply EAFP pattern to other file operations like `resume.json` or logs if they become bottlenecks.

## 2024-05-23 - [Redundant Syscalls in Hot Paths]
**Learning:** `mkdir(exist_ok=True)` is cheap but not free (~0.04ms). In hot paths like logging (called every tick/action), calling it repeatedly adds up.
**Action:** Move filesystem setup code inside initialization blocks (e.g., inside `if not logger.handlers:`) to ensure it runs only once per process.

## 2024-05-24 - [Optimistic Write for Messaging]
**Learning:** `write_outbox_entry` is a critical hot path (called for every message). Checking/creating the directory on every write added significant overhead (~50% of operation time).
**Action:** Applied the optimistic write pattern (try write -> catch FileNotFoundError -> mkdir -> retry) to `write_outbox_entry` and `FileWriteTool`. Benchmark showed ~2x speedup for writing messages.

## 2024-05-25 - [String Slicing vs Splitting]
**Learning:** Splitting large strings (like LLM responses) by newline using `split("\n")` creates excessive temporary objects. Using `find()` and slicing is ~16x faster for stripping markdown fences.
**Action:** Use slicing for parsing large text blocks where possible.

## 2024-05-26 - [Pathlib vs Open String paths]
**Learning:** `pathlib.Path` instantiation has overhead that is noticeably slower in hot loops than plain strings with `os.path.join`. We can gain a performance improvement by bypassing `Path` instantiation in internal paths when we just need to pass it to Python's built-in `open()`.
**Action:** When working in hot loops for file I/O operations like loading cached outbox entries, use `open()` with string paths instead of `Path` objects.

## 2024-06-12 - [Agent Discovery Directory Traversal]
**Learning:** `os.scandir` combined with deep nested directories (like `node_modules` in an agent's workspace) caused significant overhead during agent discovery in `discover_agents`. Since the architecture enforces a flat agent layout (a `resume.json` immediately inside the agent directory), recursing into subdirectories of an agent is an anti-pattern and highly inefficient.
**Action:** Halt recursion immediately once a `resume.json` is found in a directory, and explicitly skip known high-volume subdirectories (like `node_modules`, `workspace`, `memory`, `outbox`) during the initial scan to optimize filesystem traversal.
