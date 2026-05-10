## 2024-05-22 - Semantic HTML in Next.js Links
**Learning:** Nested <button> inside <Link> creates invalid HTML (<a><button></a>) which confuses screen readers. Always apply button styles directly to the Link component.
**Action:** Refactored main dashboard actions to use styled Links instead of nested buttons.

## 2024-05-23 - Missing Design Tokens & Focus Visible
**Learning:** Checking for missing design tokens (like `brand-purple`) in the CSS configuration is critical. Missing tokens can lead to silent failures in focus states (e.g., `focus:ring-brand-purple` doing nothing). Also, programmatic `focus()` in Playwright doesn't always trigger `:focus-visible`; simulated keyboard navigation (Tab) is more reliable.
**Action:** Added missing `brand-purple` to globals.css and used `page.keyboard.press("Shift+Tab")` for verification.

## 2025-03-08 - Maintain Aria Labels on Disabled Buttons
**Learning:** Changing the `aria-label` entirely based on disabled state (e.g. from "Next Step" to "Please fill out required fields") is an accessibility anti-pattern. Screen reader users lose the context of what the button does. Additionally, adding the native `disabled={true}` attribute removes the button from the tab sequence altogether, meaning keyboard-only screen reader users might not discover the button or its `aria-label` at all. To make disabled states fully discoverable, use `aria-disabled="true"`, style it appropriately, and manually prevent the action in the `onClick` handler, while keeping it focusable.
**Action:** Kept the primary `aria-label` ("Continue to [Next Step] step") statically defined, used `aria-disabled={!canProceedToNextStep}`, removed the native `disabled` attribute so it remains focusable, and prevented execution in the `handleNext` function. Validation instructions are provided via the native `title` attribute.
## 2024-05-24 - Disabled Buttons vs Playwright
**Learning:** When writing Playwright verification scripts, note that Playwright's actionability checks consider elements with `aria-disabled="true"` as 'not enabled'. Actions like `locator.click()` or `locator.hover()` on these elements will fail with a timeout.
**Action:** To perform actions on these elements, you must bypass the actionability checks by passing `force=True` (e.g., `locator.click(force=True)` or `locator.hover(force=True)`).

## 2024-05-25 - Prevent Form Submissions with Aria-Disabled
**Learning:** When replacing the native `disabled` attribute with `aria-disabled="true"` on a `<button type="submit">` inside a form to improve keyboard navigation accessibility, you must manually prevent the default form submission. Simply having a guard in the `onSubmit` handler is generally sufficient for the form submission, but to explicitly prevent the button's native click behavior from firing, adding an `onClick` handler with `e.preventDefault()` when the disabled condition is met is safer and addresses reviewer concerns.
**Action:** Added an `onClick` handler calling `e.preventDefault()` conditionally to the ManagerChat submit button, ensuring the application is protected against unwanted submissions while keeping the button fully discoverable.

## 2024-05-25 - Linting CI Failures
**Learning:** General Python linting errors can cause the CI pipeline to fail even for frontend/UX tasks. When CI fails due to `ruff`, `black`, and `mypy` issues across the codebase, those issues must be addressed.
**Action:** Used `ruff check --fix --unsafe-fixes`, `black`, and custom scripts to fix type hints and unused variables to pass CI.
