I plan to add the missing visual "required" indicator (`*`) to the form fields that are marked as required in the Agent Wizard (`ui/app/wizard/page.tsx`).

1. Update `ui/app/wizard/page.tsx` to add `<span className="text-red-500">*</span>` next to the `AGENT_SLUG`, `TITLE`, and `DESCRIPTION` labels, as they are required fields but lack visual indicators for users.
2. Run frontend lint and build commands locally using `pnpm` to ensure no errors are introduced.
3. Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
4. Add a journal entry to `.Jules/palette.md` noting this learning about missing required indicators in forms.
5. Submit the changes using a PR format.
