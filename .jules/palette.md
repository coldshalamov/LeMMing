## 2024-05-23 - Settings Error Feedback
**Learning:** Users were "blind" to configuration save failures because the UI only showed a generic "Save Configuration" button state without visual error feedback.
**Action:** Implemented a pattern where the save button changes text ("RETRY") and color (brand-pink) upon error, paired with a descriptive alert message (`role="alert"`), making the failure state obvious and actionable. This pattern should be reused for other async form submissions.
