## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2024-05-24 - Modal Error State & Reset Interaction
**Learning:** In modals with form inputs, persistent error states can be confusing. Automatically resetting the error state (e.g., removing the error banner and reverting button text) as soon as the user starts typing in an input field (`onChange`) creates a smoother, more forgiving experience. It signals that the system is ready for a new attempt.
**Action:** Implemented `status` reset on `onChange` for API key inputs in `GlobalSettingsModal`.
