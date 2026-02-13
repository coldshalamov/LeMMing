## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2024-05-24 - Next.js Route Announcer vs Alert Role
**Learning:** Next.js injects a global route announcer with `role='alert'` and `id='__next-route-announcer__'`, causing strict mode violations in Playwright when using `get_by_role('alert')`. Queries for error alerts must be scoped to a container (e.g., `modal.get_by_role('alert')`) or filtered by text.
**Action:** Scoped error message selectors in Playwright tests to the specific container to avoid ambiguity.

## 2024-05-24 - Input Error Recovery Pattern
**Learning:** Resetting error states (`status="idle"`) on input change (`onChange`) significantly improves UX by removing stale error messages immediately as the user attempts to fix the issue, rather than waiting for another failed submission.
**Action:** Apply this pattern to all form components where validation or submission errors occur.
