## 2025-12-16 - Actionable Empty States
**Learning:** Static empty states (e.g. "Select an item") are confusing when the list is actually empty (0 items).
**Action:** Detect the "0 items" state explicitly and provide a primary Call-to-Action (e.g. "Create New") instead of a passive placeholder.

## 2025-12-16 - Log Readability
**Learning:** Raw JSON logs are difficult to scan during active monitoring, obscuring important agent actions like tool usage or thoughts.
**Action:** Use a dedicated LogMessage component that highlights semantic fields (text, thought, tool) with icons/colors and collapses the raw payload by default.
