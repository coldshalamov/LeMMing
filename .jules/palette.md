## 2025-12-15 - Interactive Graph Accessibility
**Learning:** Force-directed graphs often rely solely on mouse interactions (`onClick`), excluding keyboard users.
**Action:** Always ensure graph nodes are keyboard-focusable (`tabIndex={0}`) and have appropriate ARIA roles (`role="button"`) and key handlers (`Enter`/`Space`).
