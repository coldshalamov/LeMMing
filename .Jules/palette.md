## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2026-02-19 - Conditional Interactivity in Log Messages
**Learning:** Assigning `role="button"` and `tabIndex="0"` to a container that is only conditionally interactive creates a confusing experience for keyboard and screen reader users, as they perceive static content as actionable buttons.
**Action:** Use conditional logic (e.g., `role={canExpand ? "button" : undefined}`) to ensure accessibility attributes are only present when the element is truly interactive, and pair this with clear `aria-label` states.
