# AI Feedback — Docs Index

This folder consolidates every doc related to CodeAssist's AI feedback / AI chat feature. It replaces the scattered `AI_*.md` files that previously lived directly under `docs/` (and one duplicate-named file at the repo root).

Last reviewed against code: 2026-07-25.

## The feature has two parts

**1. Instructor AI settings** — instructors add provider API keys (OpenAI/Gemini/Claude/Ollama) at the course level, then choose a prompt and model per course or override it per assignment. Covered in [`settings-guide.md`](./settings-guide.md) (how-to/troubleshooting) and the "Instructor-Facing" sections of [`architecture.md`](./architecture.md) (how it's implemented).

**2. Student-facing AI feedback** — students see AI feedback on their submissions through *either* submission path: uploading a file (`/upload_submission`) or writing/submitting in the in-browser code editor (`/submit_code`), plus interactive chat in the code editor's AI panel (`/ai_chat`). Both submission paths call the same `async_get_ai_feedback` pipeline. Covered in [`architecture.md`](./architecture.md) (data flow / backend) and [`code-editor-feedback.md`](./code-editor-feedback.md) (the code editor UI, its AI chat panel, and manual QA steps).

## Start here

| Doc | What it's for |
|---|---|
| [`architecture.md`](./architecture.md) | How the feature actually works today: data flow, DB tables, modules, endpoints. Read this first. |
| [`settings-guide.md`](./settings-guide.md) | Instructor side: configuring providers/models/keys per course or assignment, testing them, troubleshooting common provider errors. |
| [`code-editor-feedback.md`](./code-editor-feedback.md) | Student side: the code editor, its AI chat panel, Run/Submit flow, and how submission feedback surfaces there. Includes manual QA steps. |
| [`design-history/`](./design-history/) | Historical design docs (issue-specific rationale, the original whole-product founding doc, and the original rubric-based draft). Useful for "why is it built this way," not for "how does it work now." |
| [`known-limitations.md`](./known-limitations.md) | Product-wide known-incomplete areas (Edit Outline, Create Rubric, Grading Dashboard) — kept here because "Create Rubric" is the last trace of the abandoned rubric-grading design. |
| [`proposals/`](./proposals/) | Unimplemented feature proposals (currently: ChatALL multi-model side-by-side chat). Not part of the shipped product. |

Note: file-upload submissions get AI feedback the same way code-editor submissions do (same backend pipeline), they just don't have their own doc — there's no separate "AI panel" UI for uploads, feedback shows up on the results page. See `architecture.md` for the shared pipeline both paths go through.

## Current state summary (as of this review)

**Working and matches its docs:**
- Code-editor and file-upload submissions both trigger async AI feedback (`ai_feedback/integration.py`) with structured JSON output (`insights` + line `annotations`), three selectable feedback styles, and instructor-defined prompts.
- `/ai_chat` chat memory: last 20 messages from `ai_chat_messages` are loaded and included in every prompt. Covered by `test_ai_chat_prompt_content.py`.
- Instructor input-permission toggles (`ai_allowed_inputs`: assignment_description, student_code, test_results, test_cases, student_output) are enforced for submission-triggered feedback via `build_allowed_feedback_context()`.
- Per-student usage limits (`ai_feedback_max_requests`, `ai_feedback_wait_seconds`) are enforced server-side and tested.
- Multi-provider support (OpenAI, Gemini, Claude, Ollama) with provider-specific retry/error handling.

**Known gaps found during this review (not yet reflected as fixed anywhere):**

1. **Instructors have no working way to give the AI the assignment text.** `Assignment` has no `description` column in `api/models.py`, `CreateAssignment.js` has no description/instructions field, and `AssignmentSchema` doesn't serialize one. Backend code (`ai_feedback/settings.py::_assignment_description()`) calls `getattr(assignment, "description", "")`, which always silently returns `""` and falls back to just the assignment's *name*. The AI never sees the actual assignment requirements. The one unit test that appears to cover this (`test_ai_chat_prompt_content.py`) passes only because it mocks `.description` on a `Mock()` object rather than a real DB-backed `Assignment`.
2. **`/ai_chat` doesn't honor the instructor's `ai_allowed_inputs` toggles.** Submission feedback (`async_get_ai_feedback`) correctly filters context through `build_allowed_feedback_context()`. The interactive chat endpoint in `routes/code_editor.py` builds its own context inline instead, so disabling an input for the assignment has no effect on what the chat endpoint sends.
3. **File upload + `.zip` submissions likely break AI feedback.** `async_get_ai_feedback` opens the submitted file with `open(file_path, "r").read()` to get code text. A `.zip` upload will fail to decode as text, get caught by the generic exception handler, and the student sees a generic "AI feedback could not be generated" message instead of real feedback. No test currently covers this path.
4. **"Submission history" sent to the AI is much thinner than the naming suggests.** `student.coding_insights` is a single string that gets *overwritten* on every submission (`update_submission_feedback()`), not accumulated. So "past insights" in a new prompt only ever reflect the most recent submission's AI feedback, not a real history, and never include prior code/diffs. This matches the PR notes: "Previous submissions do not seem fully included yet."

See `architecture.md` for where each of these lives in the code, and treat items 1–3 as candidate follow-up fixes; item 4 is effectively the open "Future work 2: student history / AI memory" item already tracked separately.

## Full current AI-related endpoint list

Student-facing (`routes/code_editor.py`, `routes/submission.py`):
- `POST /submit_code`, `POST /run_code`, `POST /ai_chat`, `GET /ai_feedback_status`
- `POST /upload_submission` (also triggers AI feedback)
- `GET /assignments/<assignment_id>/prompts` (enabled prompts for a student)

Instructor-facing (`routes/ai_feedback.py`, `routes/course.py`, `routes/assignment.py`):
- `GET/PUT /assignments/<assignment_id>/ai-settings`
- `PUT /update_assignment` (accepts AI settings fields too, via `split_ai_settings_payload`)
- `PUT /store_api_key`, `PUT /update_ai_settings`, `POST /fetch_ai_models`, `POST /test_ai_api_key`, `POST /test_ai_model` (course-level)

Note: the original `docs/AI_Design_Doc.md` (now archived under `design-history/`) describes `/assignments`, `/rubrics`, `/results/{result_id}`, and `/models` endpoints and a rubric-based feedback model — **none of that was actually built**. The real system uses the endpoints above with prompt/insight JSON, not rubrics.
