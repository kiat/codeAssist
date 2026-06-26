# Issue 327 AI Feedback Settings Design

## Goal

Issue #327 adds assignment-level instructor controls for AI feedback prompts and AI input permissions. It extends the existing course-level provider settings and assignment-level model overrides without changing the student-facing AI feedback flow owned by Issue #328.

## Scope

Included in #327:

- Instructor can configure feedback prompts per assignment.
- Each prompt has an id, title, instruction text, and enabled flag.
- Instructor can configure which assignment/submission inputs may be sent to AI.
- Assignment settings are saved and loaded per assignment.
- Backend enforces allowed inputs during existing submission feedback generation.
- Existing provider/model/style/temperature settings continue to work.

Deferred to #328:

- Student prompt picker UI.
- Student-facing fetch of enabled prompts.
- Sending prompt_id from the student AI assistant.
- Uploaded .py/.zip feedback request selection.
- AIChatPanel integration changes.

## Data Model

The existing `Assignment` model remains the owner of assignment-level AI settings.

New JSON columns:

- `ai_feedback_prompts`
- `ai_allowed_inputs`

Existing assignment AI fields stay in place:

- `ai_feedback_enabled`
- `use_course_ai_default`
- `ai_feedback_provider`
- `ai_feedback_model`
- `ai_feedback_prompt`
- `ai_feedback_temperature`
- `ai_feedback_style`

`ai_feedback_prompt` is kept for backwards compatibility with PR #310/#311. When old assignments only have this single prompt, the backend normalizes it into a single enabled prompt with id `legacy_feedback_prompt`.

## Backend Design

The shared backend contract lives in `backend/ai_feedback/settings.py`.

Responsibilities:

- Define default prompt and allowed-input values.
- Normalize stored JSON and legacy prompt data.
- Validate instructor updates.
- Split assignment update payloads from AI settings payloads.
- Select an enabled feedback prompt.
- Build the AI context using only approved inputs.
- Serialize assignment AI settings consistently for both old and new endpoints.

This keeps `routes/assignment.py` thin and gives Issue #328 one backend module to reuse.

## API Design

New endpoints:

- `GET /assignments/<assignment_id>/ai-settings`
- `PUT /assignments/<assignment_id>/ai-settings`

The existing `GET /get_assignment` response also includes normalized `feedback_prompts` and `allowed_inputs`, so the current assignment settings page can load everything in one request.

The existing `PUT /update_assignment` endpoint accepts the new fields too. It delegates prompt/input validation to `ai_feedback/settings.py`.

## Frontend Design

The reusable instructor UI lives in:

- `frontend/src/components/AIFeedbackSettingsSection.js`

Frontend constants and normalization helpers live in:

- `frontend/src/constants/aiFeedbackSettings.js`

The assignment settings page wires in the reusable component and keeps page-level responsibilities such as loading the assignment, saving the assignment, and navigation.

This avoids placing prompt-list logic directly in `frontend/src/pages/assignmentSettings/index.js` and keeps future merge conflicts smaller.

## Backend Enforcement

Existing async submission feedback generation now calls:

- `get_enabled_feedback_prompt(...)`
- `build_allowed_feedback_context(...)`

The prompt sent to the AI provider is rendered from backend-approved context only. If the instructor disables student code, test cases, student output, or other inputs, those values are excluded even if frontend code has access to them.

## Default Prompts

Default prompts:

- Check correctness
- Debug failed tests
- Review edge cases
- Explain runtime errors
- Review code style
- Suggest algorithmic improvements

Defaults are provided when an assignment has no saved prompt configuration.

## Input Permissions

Supported permission keys:

- `assignment_description`
- `student_code`
- `test_results`
- `test_cases`
- `student_output`

Unknown input-permission keys are ignored. During validated writes, supported keys must be booleans.

## Testing

Backend tests cover:

- Default prompt normalization.
- Legacy single-prompt normalization.
- Invalid prompt rejection.
- Disabled prompt rejection.
- Allowed-input default merging.
- Backend context filtering.
- Assignment AI settings serialization.
- New GET/PUT assignment AI settings endpoints.
- Shared request-payload splitting.

Frontend tests cover:

- Rendering prompt settings and input permission controls.
- Adding a new prompt.
- Existing Create Assignment AI default prompt behavior.

## Merge Notes

Issue #328 should reuse `GET /assignments/<assignment_id>/ai-settings` and the normalized `feedback_prompts` payload. It should not duplicate prompt normalization or permission enforcement. When #328 adds student-selected `prompt_id`, backend validation should call `get_enabled_feedback_prompt(assignment, prompt_id)` from `backend/ai_feedback/settings.py`.
