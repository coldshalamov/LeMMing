## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2025-02-03 - Error State Patterns
**Learning:** For modal forms, simple toast notifications often miss context. Integrating the error state directly into the modal with a persistent banner (role="alert") and transforming the primary action button to "RETRY" provides clearer, more accessible feedback than a transient toast. Resetting this state on user input encourages correction.
**Action:** Adopted this "persistent banner + retry button" pattern for the Global Settings modal.
