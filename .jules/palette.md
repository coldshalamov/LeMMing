## 2024-05-24 - Interactive Graph Accessibility
**Learning:** Graph visualizations often neglect keyboard users. Interactive nodes implemented as `div`s must have `tabIndex={0}`, `role="button"`, `onKeyDown` handlers (for 'Enter' and 'Space'), and visual focus states to be accessible.
**Action:** Always wrap interactive graph nodes in button-like semantics or use actual `<button>` elements if possible, and ensure focus rings are visible against the canvas background.
