## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2024-05-27 - Interactive SVG Accessibility
**Learning:** Custom interactive SVG components (like clocks/gauges) often default to `role="button"` which requires repetitive tabbing. Using `role="radiogroup"` with roving tabindex and arrow key navigation provides a much more intuitive experience for keyboard users.
**Action:** Refactored `ScheduleClock` to use `role="radio"` and implemented arrow key navigation with focus management.
