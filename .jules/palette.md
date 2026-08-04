## 2024-07-27 - Fix Phantom Buttons in Conditional Interactions
**Learning:** Applying button roles and tab indices to conditionally interactive elements (like log rows) creates "phantom buttons" and screen reader noise when they aren't actively interactable.
**Action:** Conditionally apply `role="button"` and `tabIndex={0}` only when elements are actively interactable.
