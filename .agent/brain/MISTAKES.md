# Mistakes and Lessons Learned
### UI Refactor Bugs (2025-12-25)
- **Missing containerRef**: Accidentally removed `containerRef` and `positions` state when refactoring OrgGraph, causing crash. Fixed by restoring simulation logic.
- **Inverted Zoom Buttons**: + button zoomed out, - button zoomed in. Fixed by swapping scale multiplication logic.
- **Wizard Header Overflow**: Step indicators too wide, causing horizontal scroll on small viewports. Fixed by reducing padding and hiding labels on mobile.
- **Always test in browser**: Should have used browser_subagent to test changes immediately instead of assuming code would work.
*This file tracks mistakes made during development and lessons learned to prevent repetition.*

### Template for entries:
```
## Mistake: [Brief title]
**Date:** YYYY-MM-DD
**What happened:** [Description]
**Root cause:** [Why it happened]
**Fix:** [What was done to fix it]
**Prevention:** [How to avoid in future]
```
