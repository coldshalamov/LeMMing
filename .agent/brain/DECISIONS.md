# Architectural Decisions Log

## Decision 1: JSON-Only Resume ABI
**Date:** Pre-2025-12-25 (prior work)
**Decision:** Dropped `resume.txt` support; all agents must use `resume.json`.
**Rationale:** Simplifies parsing, enables schema validation, reduces ambiguity.
**Impact:** Existing agents migrated; template updated.

## UI/UX
- **Agent Wizard**: Multi-step form for creating agents via UI, deployed via API POST.
- **Command Center Dashboard** (2025-12-25): Transformed main UI from split-pane layout to full-screen interactive graph:
  - OrgGraph fills entire viewport as background layer
  - Agent details shown in floating glassmorphic overlay (top-right)
  - Pan/zoom controls for navigating large organizations
  - Prominent "RUN ORG" control bar at bottom center
  - Removed cramped sidebar layouts for cleaner, more immersive experience

## Decision 2: Simplified Permissions Model
**Date:** Pre-2025-12-25 (prior work)
**Decision:** Permissions limited to `read_outboxes` and `tools` only. Removed `send_outboxes` and `file_access`.
**Rationale:** 
- Outbox-only messaging means agents don't need send permissions (they write to their own outbox)
- File tools sandboxed by default to workspace/shared (no per-agent overrides)
**Impact:** Cleaner resume schema; docs need updating.

## Decision 3: Sandbox-First File Tools
**Date:** Pre-2025-12-25 (prior work)
**Decision:** All file tools restricted to `agents/<name>/workspace/` and `shared/` folders.
**Rationale:** Prevents path traversal attacks; consistent security model.
**Impact:** Tools enforce path canonicalization; legacy `file_access` removed.

---
*Add new decisions below as they are made.*
