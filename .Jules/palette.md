## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.
## 2025-03-03 - [Agent Dashboard: Use LogMessage for Recent Activity]
**Learning:** Found a micro-UX opportunity in the Agent Dashboard (`ui/app/page.tsx`). The "Recent Activity" section was rendering raw JSON payload text directly as text. Replacing it with the existing `LogMessage` component not only visually formats the activity based on its `kind` (thought, tool, report, status) and provides icons/colors, but also allows users to expand objects, copy JSON easily, and improves accessibility.
**Action:** Used `LogMessage` in the "Recent Activity" list, leveraging an existing component for a consistent, accessible UX instead of manual string rendering.
