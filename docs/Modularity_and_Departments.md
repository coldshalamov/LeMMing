# Modularity and Departments

LeMMing treats folders as first-class modules. Copying a folder (or a bundle of them) is enough to replicate a working department.

## What is a department?
A **department** is a bundle of agent folders that cooperate via `read_outboxes` permissions. Drop the bundle into `agents/` and the internal wiring reappears because each resume declares who it can read.

Examples:
- **Marketing department:** `planner`, `researcher`, `writer` with shared access to a `shared/marketing` folder.
- **Research department:** `lead`, `reader`, `summarizer` that read each other’s outboxes and store findings in memory.
- **Coding department:** `planner`, `coder`, `reviewer` with filesystem tools enabled for code generation.

## Copy/paste replication
1. Copy the department folder(s) into another LeMMing org.
2. Ensure any referenced paths in `file_access` exist (e.g., `shared/` subfolders).
3. Run `python -m lemming.cli bootstrap` to create missing directories and credit entries.
4. Start the engine; the org graph emerges automatically from `permissions.read_outboxes`.

Because the ABI is file-based, departments can be versioned, shared, or published as templates without migrations or hidden database state.

## Template and marketplace potential
- **Templates:** Ship curated bundles (e.g., "Docs Department") with prefilled resumes and sensible schedules.
- **Marketplace (future):** Let users browse and import third-party departments; the engine simply unpacks folders and honors the declared permissions.

## Safety when importing
- The canonical name is inside each `resume.json`; folder names are hints only. If two agents share a name, the duplicate is skipped with a warning.
- Invalid resumes are skipped; the rest of the department still loads.
- Tools and file allowlists remain local to each resume, so copied departments cannot escalate access beyond what their resumes declare.
