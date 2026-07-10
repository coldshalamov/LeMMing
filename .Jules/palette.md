## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2025-03-08 - Maintain Aria Labels on Disabled Buttons
**Learning:** Changing the `aria-label` entirely based on disabled state (e.g. from "Next Step" to "Please fill out required fields") is an accessibility anti-pattern. Screen reader users lose the context of what the button does. Additionally, adding the native `disabled={true}` attribute removes the button from the tab sequence altogether, meaning keyboard-only screen reader users might not discover the button or its `aria-label` at all. To make disabled states fully discoverable, use `aria-disabled="true"`, style it appropriately, and manually prevent the action in the `onClick` handler, while keeping it focusable.
**Action:** Kept the primary `aria-label` ("Continue to [Next Step] step") statically defined, used `aria-disabled={!canProceedToNextStep}`, removed the native `disabled` attribute so it remains focusable, and prevented execution in the `handleNext` function. Validation instructions are provided via the native `title` attribute.
## 2024-05-11 - Dynamic Disabled Button States
**Learning:** Icon-only async submit buttons in this app often hardcode `disabled:cursor-not-allowed` even when loading, which confuses users into thinking the form is broken rather than processing.
**Action:** Always conditionally use `cursor-wait` during async operations and provide descriptive `title` tooltips explaining the exact reason a button is disabled.

## 2026-07-10 - Contextual Tooltips for Disabled Buttons
**Learning:** Native `disabled` buttons can be confusing for users if the reason for being disabled isn't immediately obvious (e.g., missing API keys vs loading). While aria-disabled is sometimes needed to keep a button in the tab order, if keeping it native, providing dynamic `title` tooltips and contextual cursor states (`cursor-wait` vs `cursor-not-allowed`) significantly improves immediate clarity for sighted users.
**Action:** Added conditional tooltips and cursor classes via `clsx` to the Global Settings save button while retaining the native disabled attribute and adding `focus-visible` utility rings.
