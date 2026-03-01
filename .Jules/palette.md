## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2026-03-01 - Terminal Action Buttons ARIA Labels
**Learning:** In multi-step workflows like the Wizard, final action buttons (like 'Deploy Agent') often lack the explicit `aria-label` and `title` descriptions that standard navigation buttons (like 'Next' or 'Back') have. This creates an inconsistent screen reader experience.
**Action:** Added explicit `aria-label` and `title` to the Deploy Agent button to match navigation button accessibility.
