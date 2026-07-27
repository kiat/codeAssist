# AI Feedback Architecture

> Corrected/updated from the original `docs/AI_Feedback_Architecture.md`. See `README.md` in this folder for the current implementation status.

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
- **Input permission control** — instructors choose which data categories (code, test results, test cases, output, description, submission history) may reach the AI for both submission feedback and AI chat.

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
    1. Extract source code from file_path using ai_feedback.source_extraction.
       Supports normal source files and ZIP archives.
    2. Load submission/assignment/course/student via fetch_submission_data()
    3. Bail out if assignment.ai_feedback_enabled is False
    4. Load previous submission feedback history through StudentSubmissionInsight.
       Legacy coding_insights remains for compatibility.
    5. Resolve enabled prompt (get_enabled_feedback_prompt) + feedback style + provider/model/temperature
    6. build_allowed_feedback_context(assignment, code_text, autograder_results)
       → filters by assignment.ai_allowed_inputs
    7. build_feedback_prompt(...) → full prompt string
    8. Call provider (OpenAI / Gemini / Claude / Ollama) → parse JSON
    9. update_submission_feedback(): saves submission.ai_feedback and creates a
       StudentSubmissionInsight history record
```

### Data flow — AI chat (`POST /ai_chat`)

```
Student Code Editor → AIChatPanel → POST /ai_chat
    ↓
1. Verify student + enrollment
2. Check feedback limits (check_feedback_limits: max_requests, wait_seconds)
3. Resolve instructor prompt by prompt_id (optional)
4. Load chat_history = get_chat_history(student_id, assignment_id, limit=20)
5. Build context through shared AI feedback context generation.
   The same permission filtering logic is used by:
   - submission feedback
   - AI chat
   Instructor ai_allowed_inputs settings are respected consistently.
6. Call provider → get reply
7. store_chat_message() for both the user turn and the assistant reply
8. record_feedback_request() for rate limiting
9. Return { reply, feedback_status }
```

### Database Tables

| Table | Purpose |
|-------|---------|
| `users` | Includes legacy `coding_insights` for compatibility with older submission feedback history. |
| `assignments` | Stores assignment information and AI configuration. Important fields include `description`, `ai_feedback_enabled`, `ai_allowed_inputs`, `ai_feedback_prompts`, and provider/model configuration. |
| `courses` | Course-level AI defaults: provider, model, encrypted API keys, default style/temperature. Also has its own `description` column (unrelated to assignment description — do not confuse the two). |
| `ai_feedback_requests` | Per-student request log used for limit/cooldown enforcement |
| `ai_chat_messages` | Student-AI conversation history (`student_id`, `assignment_id`, `role`, `content`, `prompt_id`, `created_at`) |
| `submissions` | `ai_feedback` column stores the JSON feedback for that submission |
| `student_submission_insights` | Structured AI feedback history per submission (`student_id`, `assignment_id`, `submission_id`, `insights`, `summary`, `created_at`) |

### Backend Modules

| Module | Responsibility |
|--------|---------------|
| `ai_feedback/settings.py` | Prompt normalization, allowed-input normalization/filtering, usage-limit checks, chat history read/write, request tracking |
| `ai_feedback/source_extraction.py` | Safe source extraction for AI feedback from normal source files and ZIP archives |
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
| `CreateAssignment.js` / `assignmentSettings/index.js` | Assignment description and assignment-level AI configuration UI |

## Chat Memory

- Every user/assistant turn is stored in `ai_chat_messages`, tagged with `prompt_id` when one was used.
- Messages are stored concisely — the raw user message only, not the instructor prompt text or the full code — to keep the table lean.
- `get_chat_history(student_id, assignment_id, limit=20)` returns the **last 20** messages, chronological order, and they're folded into the `/ai_chat` prompt as "Previous conversation."
- Storage failures are caught and logged; they don't fail the chat response itself.
- **Note:** submission feedback history is stored separately from chat history (see below).

## "Coding Insights" (submission-level memory)

- Student submission history is now stored using `StudentSubmissionInsight`.
- Each AI-feedback-bearing submission creates a separate history record with structured insights and a summary.
- The previous `coding_insights` field remains for compatibility but is no longer the primary history storage mechanism.
- Submission history can be included in both submission feedback and `/ai_chat` when instructor input permissions allow it.

## Reference Solution Comparison

The `compare_to_optimal_solution` default prompt asks the model, in a single call, to:
1. Read the assignment description when it is available and permitted by `ai_allowed_inputs`.
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
| `assignment_description` | on | yes | yes |
| `student_code` | on | yes | yes |
| `test_results` | on | yes | yes |
| `test_cases` | off | yes | yes |
| `student_output` | on | yes | yes |
| `previous_submission_feedback` | on | yes | yes |

Both submission feedback and `/ai_chat` route context through the shared allowed-input filtering logic, so instructor permissions are applied consistently.

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
| `d6e7f8a9b0c1` | Assignment description field |
| `e6f7a8b9c0d2` | Student submission insight history |

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

### Regression coverage
- DB-backed assignment description creation, serialization, and AI-context behavior.
- ZIP source extraction and async AI feedback for ZIP submissions.
- `/ai_chat` permission filtering through shared allowed-input context generation.
- Submission feedback history through `StudentSubmissionInsight`.
