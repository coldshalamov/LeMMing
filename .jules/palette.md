## 2025-12-15 - Interactive Graph Accessibility
**Learning:** Force-directed graphs often rely solely on mouse interactions (`onClick`), excluding keyboard users.
**Action:** Always ensure graph nodes are keyboard-focusable (`tabIndex={0}`) and have appropriate ARIA roles (`role="button"`) and key handlers (`Enter`/`Space`).

## 2025-12-16 - Toggle Button Accessibility
**Learning:** Icon-only or custom toggle buttons (like tool selectors) often lack semantic state feedback for screen readers.
**Action:** Use `aria-pressed={isActive}` on toggle buttons to explicitly communicate their state, and ensure `type="button"` is set to prevent accidental form submission.

## 2025-12-16 - Actionable Empty States
**Learning:** Static empty states (e.g. "Select an item") are confusing when the list is actually empty (0 items).
**Action:** Detect the "0 items" state explicitly and provide a primary Call-to-Action (e.g. "Create New") instead of a passive placeholder.

## 2025-12-17 - Visual Confirmation for Toggle States
**Learning:** Relying solely on color change (e.g., gray to cyan) to indicate "active" state fails for color-blind users and lacks clarity.
**Action:** Supplement color changes with explicit visual indicators, such as a checkmark icon or shape change, when a toggle button is active.
