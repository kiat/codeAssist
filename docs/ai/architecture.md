# AI Feedback Architecture

> Corrected/updated from the original `docs/AI_Feedback_Architecture.md`. See `README.md` in this folder for a summary of open gaps found during the 2026-07-25 review.

## Overview

CodeAssist provides AI-powered feedback to students on their programming submissions, in two forms:

1. **Submission feedback** — automatic, structured JSON feedback (`insights` + line `annotations`) generated after a code-editor or file-upload submission is graded.
2. **AI chat** — interactive, turn-by-turn conversation in the code editor's AI panel, with memory of recent turns.

The system integrates with four LLM providers: OpenAI, Gemini, Claude, and Ollama (self-hosted/local).

## Key Features

- **Assignment-level AI configuration** — instructors configure prompts, allowed inputs, provider/model, temperature, feedback style, and usage limits per assignment (or inherit course defaults).
- **Student prompt selection** — students can pick from instructor-enabled feedback prompts when chatting.
- **Chat memory** — the last 20 turns of a student's chat for an assignment are replayed into each new request.
- **Reference-solution-style comparison** — one built-in prompt (`compare_to_optimal_solution`) asks the model to derive an optimal approach internally and compare the student's code against it, without a stored reference solution.
- **Per-student usage limits** — max requests and cooldown seconds enforced server-side.
- **Input permission control** — instructors choose which data categories (code, test results, test cases, output, description) may reach the AI — **for submission feedback only, see gap #2 in `README.md`.**

## Architecture

### Data flow — submission feedback

```
Student submits (code editor /submit_code, or file upload /upload_submission)
    ↓
Autograder runs in Docker → results.json
    ↓
Submission row saved (ai_feedback = None)
    ↓
Background thread: async_get_ai_feedback(app, submission_id, file_path, results_json)
    1. Read code_text from file_path  ← breaks for .zip uploads, see README gap #3
    2. Load submission/assignment/course/student via fetch_submission_data()
    3. Bail out if assignment.ai_feedback_enabled is False
    4. past_insights = student.coding_insights (a single overwritten string, see README gap #4)
    5. Resolve enabled prompt (get_enabled_feedback_prompt) + feedback style + provider/model/temperature
    6. build_allowed_feedback_context(assignment, code_text, autograder_results)
       → filters by assignment.ai_allowed_inputs
    7. build_feedback_prompt(...) → full prompt string
    8. Call provider (OpenAI / Gemini / Claude / Ollama) → parse JSON
    9. update_submission_feedback(): saves submission.ai_feedback, overwrites student.coding_insights
```

### Data flow — AI chat (`POST /ai_chat`)

```
Student Code Editor → AIChatPanel → POST /ai_chat
    ↓
1. Verify student + enrollment
2. Check feedback limits (check_feedback_limits: max_requests, wait_seconds)
3. Resolve instructor prompt by prompt_id (optional)
4. Load chat_history = get_chat_history(student_id, assignment_id, limit=20)
5. Build context manually in routes/code_editor.py:
   - assignment.description (always "" today — no DB column, see README gap #1)
   - student.coding_insights
   - previous conversation turns
   NOTE: this path does NOT call build_allowed_feedback_context(), so
   ai_allowed_inputs toggles have no effect here (README gap #2).
6. Call provider → get reply
7. store_chat_message() for both the user turn and the assistant reply
8. record_feedback_request() for rate limiting
9. Return { reply, feedback_status }
```

### Database Tables

| Table | Purpose |
|-------|---------|
| `users` | `coding_insights` column: **last** AI feedback's insight list as a string (overwritten each submission, not accumulated) |
| `assignments` | AI settings: `ai_feedback_enabled`, `use_course_ai_default`, provider/model/temperature/style overrides, `ai_feedback_prompts` (JSON), `ai_allowed_inputs` (JSON), usage limits. **No `description` column.** |
| `courses` | Course-level AI defaults: provider, model, encrypted API keys, default style/temperature. Also has its own `description` column (unrelated to assignment description — do not confuse the two). |
| `ai_feedback_requests` | Per-student request log used for limit/cooldown enforcement |
| `ai_chat_messages` | Student-AI conversation history (`student_id`, `assignment_id`, `role`, `content`, `prompt_id`, `created_at`) |
| `submissions` | `ai_feedback` column stores the JSON feedback for that submission |

### Backend Modules

| Module | Responsibility |
|--------|---------------|
| `ai_feedback/settings.py` | Prompt normalization, allowed-input normalization/filtering, usage-limit checks, chat history read/write, request tracking |
| `ai_feedback/integration.py` | Provider calls (OpenAI/Gemini/Claude/Ollama), prompt construction, JSON response parsing/repair, async submission-feedback orchestration |
| `routes/code_editor.py` | Student-facing: `/save_code_draft`, `/get_code_drafts`, `/get_latest_draft`, `/submit_code`, `/run_code`, `/ai_chat`, `/ai_feedback_status` |
| `routes/submission.py` | `/upload_submission` and other file-upload/grading endpoints, also triggers `async_get_ai_feedback` |
| `routes/ai_feedback.py` | `GET/PUT /assignments/<id>/ai-settings`, `GET /assignments/<id>/prompts` |
| `routes/assignment.py` | `/update_assignment`, `/create_assignment`, `/get_assignment` — thin wrappers that delegate AI-setting parsing to `ai_feedback/settings.py` |
| `routes/course.py` | Course-level AI settings: `/store_api_key`, `/update_ai_settings`, `/fetch_ai_models`, `/test_ai_api_key`, `/test_ai_model` |

### Frontend Components

| Component | Role |
|-----------|------|
| `AIChatPanel.js` | Student chat interface: prompt buttons, remaining-request count, cooldown countdown |
| `AIFeedbackSettingsSection.js` | Instructor prompt/input-permission/limit configuration UI |
| `codeEditor/index.js` | Code editor page, integrates `AIChatPanel` |
| `CreateAssignment.js` / `assignmentSettings/index.js` | Assignment-level AI config UI (no assignment description/instructions field today) |

## Chat Memory

- Every user/assistant turn is stored in `ai_chat_messages`, tagged with `prompt_id` when one was used.
- Messages are stored concisely — the raw user message only, not the instructor prompt text or the full code — to keep the table lean.
- `get_chat_history(student_id, assignment_id, limit=20)` returns the **last 20** messages, chronological order, and they're folded into the `/ai_chat` prompt as "Previous conversation."
- Storage failures are caught and logged; they don't fail the chat response itself.
- **Note:** `student.coding_insights` is a *separate*, much shallower mechanism (see below) — it is not the same thing as chat memory.

## "Coding Insights" (submission-level memory)

- Populated only by `update_submission_feedback()` after a submission gets AI feedback: `student.coding_insights = str(new_insights)`.
- This **replaces** the previous value; it does not append or summarize across submissions.
- Used as `past_insights` in the next submission's feedback prompt, and also surfaced into `/ai_chat` context as "Student coding history."
- Practical effect: a student's "history" as seen by the AI is really just "what the AI said last time," not a durable multi-submission record. This is the gap tracked as "Future work 2: student history / AI memory."

## Reference Solution Comparison

The `compare_to_optimal_solution` default prompt asks the model, in a single call, to:
1. Read the assignment description (today: usually just the assignment name, see gap #1).
2. Internally derive an optimal approach.
3. Compare the student's code against it (algorithmic differences, complexity, structure).
4. Give feedback without revealing the derived solution or providing copy-paste fixes.

There is no separately stored/generated reference solution artifact — this is prompt-engineering only, done fresh on each request.

## Usage Limits

| Setting | Meaning |
|---------|---------|
| `ai_feedback_max_requests` | Max AI requests per student per assignment. `null` = unlimited, `0` = disabled. |
| `ai_feedback_wait_seconds` | Cooldown between requests. `0` = no wait. |

Enforced server-side in `check_feedback_limits()` before every `/ai_chat` call; `get_student_feedback_status()` returns the current remaining/wait state for the frontend countdown UI.

## Input Permissions (`ai_allowed_inputs`)

| Permission | Default | Applies to submission feedback | Applies to `/ai_chat` |
|-----------|---------|:---:|:---:|
| `assignment_description` | on | yes | no — built inline, always attempted (see gap #1: usually empty anyway) |
| `student_code` | on | yes | no — always sent |
| `test_results` | on | yes | no — not sent to chat at all today |
| `test_cases` | off | yes | no — not sent to chat at all today |
| `student_output` | on | yes | no — not sent to chat at all today |

Recommendation: if this matters for your rollout, either route `/ai_chat` through `build_allowed_feedback_context()`/`render_feedback_context()` like submission feedback does, or document explicitly that input permissions currently only govern submission feedback.

## Default Prompts

Nine built-in prompts ship in `ai_feedback/settings.py::DEFAULT_AI_FEEDBACK_PROMPTS` (all enabled by default, instructors can edit/disable/add):

1. Check correctness
2. Debug failed tests
3. Review edge cases
4. Explain runtime errors
5. Review code style
6. Suggest algorithmic improvements
7. Check code syntax
8. Compare to optimal solution
9. Personalized feedback

(Earlier design docs list only the first six — the last three were added since.)

## Migrations

| Migration | Creates |
|-----------|---------|
| `45b5cf6cc787` | Input logging columns for AI feedback |
| `b3c4d5e6f7a8` | `ai_chat_messages` table |
| `03dd583914d0` | Submission history / linked-submission tracking |

(Run `alembic history` in `backend/migrations` for the authoritative, current list — names above are as of this review.)

## Testing

### Backend
```bash
cd backend && PYTHONPATH=. python -m pytest test/unit/ --no-cov
```
Relevant files: `test_ai_chat_prompt_content.py`, `test_ai_feedback_request_tracking.py`, `test_ai_feedback_settings.py`, `test_ai_integration.py`, `test_code_editor.py`.

### Frontend
```bash
cd frontend && npx react-scripts test --watchAll=false --testPathPattern='AIChatPanel'
```

### Gaps in current test coverage (see `README.md` for detail)
- No test creates a real DB-backed `Assignment` with a `description` and confirms it reaches the prompt — existing coverage mocks the attribute directly, which can't catch a missing column.
- No test exercises `.zip` file upload through `async_get_ai_feedback`.
- No test asserts `/ai_chat` respects `ai_allowed_inputs`.
