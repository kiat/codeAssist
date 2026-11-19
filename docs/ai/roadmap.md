# AI Feedback - Improvement Roadmap

Prioritized plan based on the code review in `README.md` / `architecture.md`.
P0 = correctness/trust or security gap affecting every submission/course today;
P1 = real inconsistency worth fixing before it compounds; P2 = test-debt and
hardening; P3 = longer-term design work.

Last updated: 2026-08-06, after PR
[#365](https://github.com/kiat/codeAssist/pull/365) added Gemini over Vertex AI
support and PR [#352](https://github.com/kiat/codeAssist/pull/352) merged the
previously open assignment-description, ZIP-source-extraction, `/ai_chat`
permission-filtering, and per-submission feedback-history fixes.

Scope note: the current direction is controlled, assignment-level AI feedback:
instructors decide which prompts/questions matter for each assignment, and
students should not get an open-ended "ask the AI anything" surface.
Course-level provider/model defaults can remain useful, but prompt/question
configuration should stay at the assignment level.

## Currently Open

### P0 - Course-level AI settings endpoints need authorization checks

**Problem:** `store_api_key`, `update_ai_settings`, `fetch_ai_models`,
`test_ai_api_key`, and `test_ai_model` in `backend/routes/course.py` need
course-role authorization. Any caller who knows or guesses a `course_id` UUID
must not be able to overwrite the course's configured AI provider/model/API key
or use provider-testing routes as an oracle for arbitrary API keys.

Note: the Ollama path is **not** vulnerable to SSRF. `_request_ollama()` already
calls `validate_ollama_url()`, which enforces a hostname allowlist
(`ALLOWED_OLLAMA_HOSTS`) before making any outbound request.

**Fix:** Apply the same authorization pattern used elsewhere in the codebase:
require a session user, look up the course, and allow only the course instructor
or an enrolled `instructor` / `ta` to proceed. Apply this to all five endpoints
listed above.

**Verify:** Test that unauthenticated requests and requests from unrelated
students receive `401` / `403`, while the course instructor and a TA still
succeed.

### P1 - `store_api_key` is a confusing, OpenAI-only duplicate

**Problem:** `store_api_key` only sets `course.openai_api_key`, does not
validate `provider`, and overlaps with `update_ai_settings`, which handles all
four providers plus model/style/temperature. Keeping two partial course-AI
settings paths increases maintenance risk.

**Fix:** Confirm whether any frontend code still calls `store_api_key`
(`frontend/src/services/course.js`). If not, remove it. If it is still used,
delete it in favor of `update_ai_settings` or make it delegate to the same
shared logic instead of duplicating only the OpenAI case.

### P2 - Raw exception/provider-response text returned to the client

**Problem:** `fetch_ai_models`, `test_ai_api_key`, and `test_ai_model` return
raw exception strings or provider response text in some error paths. Raw
provider bodies and Python exception strings are not guaranteed to be safe or
useful in the browser, and this differs from the structured error pattern used
elsewhere.

**Fix:** Log raw provider/exception detail server-side, then return a structured
generic client error via the same `BadRequestError` / `InternalProcessingError`
style used in other routes.

## Recently Completed

### P1 - Gemini over Google Cloud Vertex AI support

PR [#365](https://github.com/kiat/codeAssist/pull/365) added the
`gemini_vertex` provider mode, server-managed Vertex credentials, project and
location configuration, a separate Gemini/Vertex client path, UI copy that keeps
Gemini Developer API distinct from Gemini over Vertex AI, and tests for provider
resolution plus sanitized provider errors.

### P3 - Real student-history / AI-memory design

PR [#352](https://github.com/kiat/codeAssist/pull/352) fixed the immediate
history bug by storing per-submission feedback in `StudentSubmissionInsight`
instead of overwriting a single `coding_insights` string. What remains is the
larger, deliberate memory/privacy design:

- **Structured student summaries instead of raw chat history** - e.g. a compact
  record per student per assignment with common mistake categories, improvement
  trend, and recent score signals.
- **Instructor on/off toggle for memory** - course or assignment setting, aligned
  with the existing `ai_allowed_inputs` pattern, so instructors can disable
  cross-submission personalization for exams or integrity-sensitive work.
- **Privacy controls for stored history** - retention window, student-visible
  "what the AI remembers about me" view, and deletion path.
- **Separate short-term chat context from long-term learning memory** -
  `ai_chat_messages` already covers recent conversation context; the long-term
  learning profile should be designed separately.

Scope this as its own design doc + issue. It touches data model, privacy, and
instructor UX enough that it deserves a dedicated review rather than being
bundled into a hardening PR.

### P3 - AI-generated submission-defense questions

**Problem / opportunity:** Kia suggested a more controlled student-AI
interaction: after a submission passes static tests, the AI asks the student a
targeted question about their own submitted code, and the student explains the
implementation in text or recorded audio.

**Why this fits the direction:** It checks understanding without letting
students ask for direct answers, and it can be configured per assignment around
the concepts instructors care about.

**Proposal:** See `proposals/submission-defense-questions.md` for example
questions, a possible table shape, and open design decisions.

## Shipped In PR #352

These used to be active P0/P1 roadmap items. They are listed here only so future
reviewers do not re-open stale bugs.

- **Assignment description reaches the AI.** Assignments now have a description
  field, the UI can edit it, and shared AI context generation includes it when
  `ai_allowed_inputs.assignment_description` is enabled.
- **ZIP submissions have AI source extraction.** The feedback pipeline reads
  supported source files from ZIP archives through `ai_feedback/source_extraction.py`
  instead of failing with a generic decode error.
- **`/ai_chat` respects instructor input permissions.** Chat and submission
  feedback now use the shared allowed-input context generation path.
- **Submission history is not overwritten.** Per-submission feedback history is
  stored with `StudentSubmissionInsight`; legacy `users.coding_insights` remains
  only for compatibility.
