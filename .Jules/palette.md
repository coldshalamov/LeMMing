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
## 2024-05-23 - Contextual Disabled Button Styles
**Learning:** For disabled async buttons, providing an accurate visual cue via pointer states is critical. If a button is disabled because a process is ongoing (e.g., `status === "loading"`), use `cursor-wait` to indicate that the system is working. If it is disabled due to missing requirements (e.g., missing API keys), use `cursor-not-allowed`. This provides immediate, non-verbal feedback to the user about why the interaction is blocked. Combined with `aria-disabled="true"` and an informative `title` attribute, this ensures both visual and assistive technology users have complete context.
**Action:** When implementing `aria-disabled` logic, conditionally map the Tailwind cursor classes based on the exact reason for the disabled state (`cursor-wait` vs `cursor-not-allowed`) rather than applying a blanket style.
