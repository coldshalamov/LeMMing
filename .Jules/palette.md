## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2024-05-24 - Escape Key Support & Keyboard Navigation
**Learning:** For overlays or modals created using standard React states (like `selectedAgentName` showing details), native Escape key functionality is missing unless explicitly implemented via `useEffect` event listeners. Moreover, providing proper keyboard focus indicators (`focus-visible:ring-2` etc.) on links and buttons ensures clarity for non-mouse users navigating these interfaces.
**Action:** When implementing new temporary UI states or interactive elements without native HTML accessible defaults, immediately consider Escape-to-close behavior and verify clear visual focus indicators.
