## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2024-05-24 - Multi-step Terminal Actions
**Learning:** Terminal action buttons in multi-step workflows (like 'Deploy Agent' in the Wizard) can become icon-only or unreadable by screen readers during loading states (e.g., when replaced by a spinner). Explicit `aria-label` and `title` attributes ensure consistent screen reader experiences and navigation accessibility regardless of the button's dynamic state.
**Action:** Always provide explicit accessible names for critical terminal navigation buttons, especially if their visual contents change dynamically during async operations.
