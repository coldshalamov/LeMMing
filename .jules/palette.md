## 2025-05-23 - SVG Accessibility Interactions
**Learning:** When making complex SVG visualizations (like a clock) interactive, standard `role="button"` or `role="radio"` on SVG groups (`<g>`) works well, but visual focus states require manual handling. CSS `focus-visible` on the group needs to trigger a child element (like a focus ring circle) using `group-focus`.
**Action:** For future custom SVG widgets, wrap interactive parts in `<g>` with `tabIndex={0}`, add keyboard handlers for Enter/Space, and use `group` + `group-focus` classes to show a custom focus indicator (ring or color change) that fits the SVG's coordinate system.

## 2025-05-23 - Nested Interactive Roles and AgentCard
**Learning:** When rendering complex statistics (like progress bars) inside a clickable `AgentCard` button, use `aria-hidden='true'` for the visual bars and decorative icons to prevent redundant or confusing screen reader announcements.
**Action:** Instead of nested roles, provide all relevant data (including stats) via the button's `aria-label` or `aria-describedby` to ensure a clean audio experience while maintaining the visual richness.

## 2025-05-25 - Modal Keyboard Accessibility
**Learning:** Custom modals (like those built with framer-motion) often lack built-in support for the Escape key, which is a critical accessibility requirement for keyboard users.
**Action:** Always add a global `keydown` listener for "Escape" in the modal's effect hook to ensure users can easily dismiss the overlay without finding the close button.

## 2025-05-25 - Focus Management in Single Page Wizards
**Learning:** In multi-step wizards implemented as a single page view, screen reader users often lose context when clicking "Next" because focus remains on the button (which might disappear) or the body.
**Action:** When the step index changes, programmatically shift focus to the new step's heading (using a `ref` and `useEffect`) so users immediately know where they are.

## 2025-05-25 - Playwright Modal and API Interception
**Learning:** When using Playwright to verify loading states in modals (like a settings screen), simply matching `page.get_by_role("button", name="SAVING...")` can fail if the button structure changes during loading (e.g., adding an SVG spinner inside). Furthermore, intercepting `**/api/*` routes generically in Next.js might inadvertently block other critical frontend assets, causing timeouts.
**Action:** When capturing transient loading states, selectively mock only the exact target API endpoint (e.g., `**/api/engine/config`) using `page.route` to prevent hanging unrelated frontend requests, and wait for robust inner locators (like `page.locator("button:disabled")` or specific SVG icons) rather than full text matching.

## 2025-05-25 - Playwright UI Automation and React Structural Changes
**Learning:** Changing a button's content from a raw string (`"SAVING..."`) to a React fragment with mixed DOM nodes (e.g. `<><Loader2 /> SAVING...</>`) breaks Playwright tests that rely on strict exact text matchers (like `name="SAVING..."`).
**Action:** When adding icons or spinners next to text in a button, wrap the bare text node in a semantic tag (e.g., `<span>SAVING...</span>`) so that automated accessibility locators and test scripts can consistently isolate and match the text label regardless of adjacent sibling DOM elements.
