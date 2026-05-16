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

## 2024-05-18 - Accurate cursor states for async actions
**Learning:** The "SAVE CONFIG" button in `GlobalSettingsModal` previously lacked visual feedback when disabled during an asynchronous save, using default cursor behavior which isn't informative.
**Action:** When a button is disabled due to a loading state, use `cursor-wait` to inform the user that the system is processing. Use `cursor-not-allowed` when the button is structurally disabled (e.g., missing required input).
