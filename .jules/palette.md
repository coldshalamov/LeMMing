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
