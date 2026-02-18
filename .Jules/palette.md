## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2024-05-24 - Controlled Inputs for Array Data
**Learning:** Directly binding an array to a text input via `join(', ')` causes immediate stripping of delimiters (commas/spaces) during typing, frustrating users. A separate "raw input" state is required to preserve the user's keystrokes while parsing the array in the background.
**Action:** Implemented a `read_outboxes_input` state variable to decouple the display value from the logical array state in the Wizard.
