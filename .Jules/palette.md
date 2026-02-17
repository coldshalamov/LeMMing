## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2026-02-17 - Error State Transparency
**Learning:** Silent failures in modal forms erode user trust. Explicitly showing an error banner with actionable advice (e.g., "Check network") and changing the primary button to "RETRY" provides clear feedback and a path forward. Clearing the error on input modification encourages correction.
**Action:** Implemented a reusable error handling pattern: Error State + Alert Banner + Retry Button + Clear-on-Edit.
