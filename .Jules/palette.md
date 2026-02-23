## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2024-05-24 - Conditional Interactivity for Accessibility
**Learning:** Interactive elements (like log message toggle) must not have interactive roles (button) or focusable tabindex when they are not actually interactive (e.g., when the log is not expandable). This avoids confusing screen reader users who expect an action but find none.
**Action:** Conditionally apply `role="button"`, `tabIndex`, and event handlers based on the interactivity state (`canExpand`).
