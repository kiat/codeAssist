# AI Feedback — Docs Index

This folder consolidates every doc related to CodeAssist's AI feedback and controlled AI prompt panel. It replaces the scattered `AI_*.md` files that previously lived directly under `docs/` (and one duplicate-named file at the repo root).

Last reviewed for PR #365: 2026-08-06.

## The feature has two parts

**1. Instructor AI settings** — instructors add provider API keys and default provider/model settings at the course level, then configure prompts, allowed inputs, usage limits, and any per-assignment provider/model overrides at the assignment level. Covered in [`settings-guide.md`](./settings-guide.md) (how-to/troubleshooting) and the "Instructor-Facing" sections of [`architecture.md`](./architecture.md) (how it's implemented).

**2. Student-facing AI feedback** — students see AI feedback on their submissions through *either* submission path: uploading a file (`/upload_submission`) or writing/submitting in the in-browser code editor (`/submit_code`), plus a controlled preset-prompt AI panel in the code editor (`/ai_chat`). Both submission paths call the same `async_get_ai_feedback` pipeline. Covered in [`architecture.md`](./architecture.md) (data flow / backend) and [`code-editor-feedback.md`](./code-editor-feedback.md) (the code editor UI, its AI panel, and manual QA steps).

## Start here

| Doc | What it's for |
|---|---|
| [`architecture.md`](./architecture.md) | How the feature actually works today: data flow, DB tables, modules, endpoints. Read this first. |
| [`settings-guide.md`](./settings-guide.md) | Instructor side: configuring providers/models/keys per course or assignment, testing them, troubleshooting common provider errors. |
| [`vertex-setup.md`](./vertex-setup.md) | Deployment setup for Gemini over Vertex AI, including API-key and ADC auth modes plus local test steps. |
| [`code-editor-feedback.md`](./code-editor-feedback.md) | Student side: the code editor, its controlled AI prompt panel, Run/Submit flow, and how submission feedback surfaces there. Includes manual QA steps. |
| [`design-history/`](./design-history/) | Historical design docs (issue-specific rationale, the original whole-product founding doc, and the original rubric-based draft). Useful for "why is it built this way," not for "how does it work now." |
| [`known-limitations.md`](./known-limitations.md) | Product-wide known-incomplete areas (Edit Outline, Create Rubric, Grading Dashboard) — kept here because "Create Rubric" is the last trace of the abandoned rubric-grading design. |
| [`proposals/`](./proposals/) | Unimplemented feature proposals. [`Submission-defense questions`](./proposals/submission-defense-questions.md) are the current exploratory direction. |
| [`roadmap.md`](./roadmap.md) | Longer-term AI feedback roadmap, new Vertex AI request, and future controlled-feedback design notes. |

Note: file-upload submissions get AI feedback the same way code-editor submissions do (same backend pipeline), they just don't have their own doc — there's no separate "AI panel" UI for uploads, feedback shows up on the results page. See `architecture.md` for the shared pipeline both paths go through.

## Current state summary (as of this review)

**Working and matches its docs:**
- Code-editor and file-upload submissions both trigger async AI feedback (`ai_feedback/integration.py`) with structured JSON output (`insights` + line `annotations`), three selectable feedback styles, and instructor-defined prompts.
- `/ai_chat` prompt-panel memory: last 20 student/assistant turns from `ai_chat_messages` are loaded and included in every request. Covered by `test_ai_chat_prompt_content.py`.
- Instructor input-permission toggles (`ai_allowed_inputs`: assignment_description, student_code, test_results, test_cases, student_output, submission_history) are enforced through shared context filtering for submission-triggered feedback and `/ai_chat`.
- Per-student usage limits (`ai_feedback_max_requests`, `ai_feedback_wait_seconds`) are enforced server-side and tested.
- Multi-provider support (OpenAI, Gemini Developer API, Gemini over Vertex AI, Claude, Ollama) with provider-specific retry/error handling.
- Gemini over Vertex AI uses deployment-managed Google Cloud credentials rather than per-course credentials. See `vertex-setup.md`.

**Requested but not implemented yet:**
- AI-generated submission-understanding questions after static tests pass, with student written or recorded explanations. This is a new future feature direction, not current behavior.

## Current implementation status

The following AI feedback improvements have been implemented:

### Assignment description support

Assignments now support instructor-provided descriptions.

The assignment description is stored in `Assignment.description` and can be configured from:

- Create Assignment
- Assignment Settings

The description is included in AI feedback context when enabled.

---

### Unified AI context permissions

Both submission feedback and `/ai_chat` use the same AI context filtering logic.

Instructor `ai_allowed_inputs` settings now apply consistently to:

- assignment description
- student code
- test results
- test cases
- student output
- submission history

---

### ZIP submission AI feedback

ZIP submissions are supported through a source extraction pipeline.

The extractor:

- reads supported source files
- validates archive paths
- limits archive size
- prevents unsafe extraction behavior

---

### Submission history memory

Previous submission feedback is stored using `StudentSubmissionInsight`.

Each submission creates its own history record instead of overwriting previous feedback.

Future improvements:

- assignment-level learning-memory controls
- student privacy controls
- instructor-controlled feedback/question configuration
- better long-term learning summaries

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
