## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2024-05-24 - Silent Failure in Modals
**Learning:** Modals that perform async actions often default to a "happy path" UI (loading -> success), but missing the "error" path leaves users confused when things fail. The learning is that "Error states in modals must be as prominent as success states, otherwise the user is stuck in a loop of clicking 'Save' without knowing why it's not working."
**Action:** Implemented explicit error state handling and rendering in `GlobalSettingsModal`.
