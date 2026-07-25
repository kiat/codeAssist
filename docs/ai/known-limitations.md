> Moved from `docs/CodeAssist_limitations.md`. This is product-wide, not AI-specific, but it's kept here because the rubric-grading gap it mentions ties directly into `design-history/original-rubric-design-draft.md` — the AI feedback system was originally designed around rubrics, and rubrics were never built. See `README.md` for the AI-specific gap list (missing assignment description, `/ai_chat` input-permission bypass, `.zip` upload feedback failure, thin submission history).

## Current Limitations

The following features are **incomplete** or use placeholder logic as part of ongoing development:

- **Edit Outline**, **Create Rubric**, and **Grading Dashboard** currently rely on hardcoded input data. These components do not yet fetch or persist assignment-related information from the backend or database and have been commented out.
  - **Create Rubric** in particular is the last visible trace of the original rubric-based grading design (see `design-history/original-rubric-design-draft.md`). The AI feedback system that actually shipped uses instructor-defined prompts instead of rubrics, so this UI is stale relative to current backend design, not just unfinished.

- Removed hardcoded UI and static data ([#134](https://github.com/your-repo/codeAssist/issues/134))
