## 2025-12-16 - Actionable Empty States
**Learning:** Static empty states (e.g. "Select an item") are confusing when the list is actually empty (0 items).
**Action:** Detect the "0 items" state explicitly and provide a primary Call-to-Action (e.g. "Create New") instead of a passive placeholder.

## 2025-12-16 - Semantic Buttons for Interactive Cards
**Learning:** Interactive cards implemented as `div`s with `onClick` handlers lack native accessibility features like keyboard support (Enter/Space) and proper focus management.
**Action:** Refactor interactive cards to use `<button>` (or `<motion.button>`) elements with `type="button"` and `text-left`, removing the need for manual `onKeyDown` handlers and `role="button"` attributes.
