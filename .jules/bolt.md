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

## $(date +%Y-%m-%d) - [O(n^2) nested loop vs HashMap in Social Graph Analysis]
**Learning:** In `analyze_social_graph`, processing every message outbox file to scan for relationships against all known relationships produced an O(n^2) loop (with `pathlib` overhead and full pydantic object instantiation to boot). Iterating JSON files via `os.scandir`, extracting minimal required fields directly (`json.load` dictionary lookup instead of `from_dict`), and keeping interactions mapped via O(1) hashes (`interaction_counts_all` and `rel_map`) improved benchmarking speeds significantly (~1.3s down to 0.25s).
**Action:** When building association tables across multiple agents repeatedly every tick (or backward windows of ticks), build relationship maps outside the loop first, use sets for single-message duplicated lists, and avoid heavy object instantiation.
