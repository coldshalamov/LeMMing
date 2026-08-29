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

## $(date +%Y-%m-%d) - [Optimizing load_agent Caching]
**Learning:** `load_agent` parses identical `resume.json` files recursively despite the `_agent_cache` initialized and used in `discover_agents`. Bypassing disk I/O reads by checking `st_mtime` can significantly decrease repetitive loading overheads.
**Action:** When working on caching functions, check if an existing cache dictionary can be reused for parallel/repeated calls rather than reparsing.
## $(date +%Y-%m-%d) - [ModelRegistry Caching]
**Learning:** Repetitive file reading and JSON parsing along with schema validation (`validate_models`) created a bottleneck when repeatedly instantiating `ModelRegistry`.
**Action:** Implemented an `mtime`-based cache (`_registry_cache`) keyed by the resolved configuration directory `self.config_dir.resolve()` to avoid redundant processing while supporting hot-reloading. Prevented cache poisoning by preserving the initial `mtime` read prior to blocking IO (`json.load`), falling back to `0` instead of breaking. Protected cached objects from mutation by returning deep `.copy()` from `self._models`.

## 2025-02-23 - Avoid fully instantiating large Dataclasses in Python Hot Loops
**Learning:** Instantiating complex Python Dataclasses (like `OutboxEntry`) in a tight hot loop (like reading 1000s of JSON files in `analyze_social_graph`) incurs high CPU overhead, especially if only a single integer field (like `tick`) is actually needed for the computation.
**Action:** Extract the needed keys directly from the raw dictionary returned by `json.load()` instead of passing the entire dictionary to `.from_dict()` when parsing bulk files.

## 2025-02-23 - Use os.scandir as a generator instead of pathlib.Path.glob
**Learning:** `Path.glob()` aggressively instantiates `Path` objects which impacts speed and memory. While `os.scandir()` is much faster because it directly yields `os.DirEntry` objects, it must be carefully wrapped in a generator expression to fully benefit from its lazy evaluation in loops, avoiding materializing the entire directory contents into memory at once.
**Action:** Replace `Path.glob()` with `(entry.path for entry in os.scandir(dir) if ...)` inside `try...except OSError` blocks for I/O-bound loops.
