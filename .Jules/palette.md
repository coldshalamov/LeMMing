## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2025-05-26 - React Array Rendering Fallbacks
**Learning:** In JSX, `array.map(...)` returns an empty array `[]` when the source is empty, which is truthy. Using the logical OR operator `||` for fallback content (e.g., `{items.map(...) || <Empty />}`) fails because the empty array is returned instead of the fallback.
**Action:** Always check `array.length > 0` explicitly or use a conditional ternary operator for empty states, rather than relying on truthiness of the map result.

## 2025-05-26 - Layout Overlaps and Interactive Elements
**Learning:** Fixed-position overlays (like `ManagerChat`) that ignore the main content grid's flow can completely occlude interactive elements (like the first `AgentCard`), making them inaccessible to mouse users and failing automated tests.
**Action:** Ensure grid layouts have sufficient margins or padding to account for fixed overlays, or use z-index aware layout systems that prevent content from sliding under persistent UI panels.
