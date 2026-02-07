## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2025-05-24 - Async Error Feedback in Modals
**Learning:** Modals performing async actions (like `updateEngineConfig`) often lack explicit error feedback, reverting to a neutral state on failure. This confuses users who think the action succeeded or was ignored.
**Action:** Always implement a dedicated error state (e.g., `status === "error"`) with a visible `role="alert"` message and a distinct "RETRY" button style to clearly communicate failure.
