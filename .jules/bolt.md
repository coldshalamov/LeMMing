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

## 2024-05-27 - [Optimizing load_agent Caching]
**Learning:** `load_agent` parses identical `resume.json` files recursively despite the `_agent_cache` initialized and used in `discover_agents`. Bypassing disk I/O reads by checking `st_mtime` can significantly decrease repetitive loading overheads.
**Action:** When working on caching functions, check if an existing cache dictionary can be reused for parallel/repeated calls rather than reparsing.

## 2024-05-27 - [Pathlib Instantiation Overhead in memory.py]
**Learning:** `pathlib.Path` instantiation inside high-frequency file I/O operations (like `save_memory` and `load_memory`) acts as a noticeable bottleneck due to the cost of constructing path objects. The string operations via `os.path.join` bypassing object instantiation are consistently much faster.
**Action:** Replaced `Path` instantiations in memory operations (`memory_file.open(...)` using `memory_dir / f"{key}.json"`) with string construction (`os.path.join(str(memory_dir), f"{key}.json")`) and standard built-in `open()`. Apply similar `Path` instantiation avoidance to other hot path file I/O operations where appropriate.
