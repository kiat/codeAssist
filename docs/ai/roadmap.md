# AI Feedback — Improvement Roadmap

Prioritized plan based on the code review in `README.md`/`architecture.md`. Each item lists the problem, the fix, the files involved, and how to verify it. P0 = correctness/trust or security gap affecting every submission/course today; P1 = real inconsistency worth fixing before it compounds; P2 = test-debt and hardening; P3 = longer-term design work (this is where your "Future work 2: student history / AI memory" notes belong).

Scope note (2026-07-25): multi-model side-by-side comparison (ChatALL, see `proposals/chatall-multi-ai.md`) is intentionally out of scope pending instructor/professor approval. Current single-provider-per-course-with-per-assignment-override design (`update_ai_settings`, `Assignment.use_course_ai_default` + overrides) is the right shape to keep — the items below are about hardening and correcting that existing design, not replacing it.

## P0 — Course-level AI settings endpoints have no authorization check

**Problem:** `store_api_key`, `update_ai_settings`, `fetch_ai_models`, `test_ai_api_key`, and `test_ai_model` in `backend/routes/course.py` never check `session.get("user_id")` or verify the requester is the course's instructor/TA. Any caller who knows or guesses a `course_id` UUID can: overwrite the course's configured AI provider/model/API key (`update_ai_settings`, `store_api_key`), or use `test_ai_api_key`/`fetch_ai_models`/`test_ai_model` as a free oracle to check whether an arbitrary OpenAI/Gemini/Claude API key is valid. This isn't unique to AI settings — `update_course`/`delete_course` in the same file have the same gap — but it's most consequential here because it directly controls what AI provider/key every submission in a course uses, and a bad actor could silently swap in a key that drains someone else's quota or breaks AI feedback for an entire course.

Note: the Ollama path is **not** vulnerable to SSRF — `_request_ollama()` already calls `validate_ollama_url()`, which enforces a hostname allowlist (`ALLOWED_OLLAMA_HOSTS`) before making any outbound request. That part is solid as-is.

**Fix:** Add the same authorization pattern already used correctly elsewhere in the codebase — `routes/ai_feedback.py::_require_instructor_or_ta_for_assignment()` and `routes/submission.py::_verify_course_staff()` are both good models to copy: require a `requester_id`/session user, look up the course, and only allow the instructor or an enrolled `instructor`/`ta` to proceed. Apply to all five endpoints listed above (and flag `update_course`/`delete_course` separately since they're the same root cause, even though they're outside the AI settings scope).

**Verify:** Test that an unauthenticated request (no session) and a request from a student (not instructor/TA) enrolled in some other course both get `403 Forbidden` from each of the five endpoints; test that the actual course instructor and a TA still succeed.

## P1 — `store_api_key` is a confusing, OpenAI-only duplicate of `update_ai_settings`

**Problem:** `store_api_key` only ever sets `course.openai_api_key`, doesn't validate `provider`, and overlaps with `update_ai_settings` (which correctly handles all four providers plus model/style/temperature). Having two endpoints that partially do the same thing is a maintenance and correctness risk — a frontend caller using the wrong one silently only ever configures OpenAI.

**Fix:** Confirm whether any frontend code still calls `store_api_key` (`frontend/src/services/course.js`); if not, remove it. If it's still used, either delete it in favor of `update_ai_settings` or make it delegate to the same logic instead of duplicating a partial version of it.

## P2 — Raw exception/provider-response text returned to the client

**Problem:** `fetch_ai_models`, `test_ai_api_key`, and `test_ai_model` all have a bare `except Exception as e: return jsonify({"error": str(e)}), 500` and, on provider HTTP errors, return `response.text` from Gemini/Claude directly to the frontend. This is low-severity but worth cleaning up — raw provider error bodies and Python exception strings aren't guaranteed to be safe to show a browser, and it's inconsistent with how errors are handled elsewhere (`util/errors.py`'s structured error responses).

**Fix:** Wrap these in the same structured-error pattern used by `BadRequestError`/`InternalProcessingError` elsewhere, logging the raw detail server-side and returning a generic message to the client.

## P0 — Assignment description doesn't reach the AI

**Problem:** `Assignment` has no `description` column (`backend/api/models.py`). `ai_feedback/settings.py::_assignment_description()` calls `getattr(assignment, "description", "")`, always gets `""`, and falls back to just the assignment name. Every AI feedback prompt and every `/ai_chat` message has been running without real assignment context since this was built. This is the single highest-impact fix — it affects grading quality on every submission, not just an edge case.

**Fix:**
1. Add an `Assignment.description` (Text) column + Alembic migration.
2. Add `description` to `AssignmentSchema` (`backend/api/schemas.py`) so it round-trips through `get_assignment`/`update_assignment`/`create_assignment`.
3. Add a textarea to `CreateAssignment.js` and the assignment settings page for instructors to enter it.
4. No change needed in `ai_feedback/settings.py` — `_assignment_description()` already reads the attribute correctly once it exists; the whole bug is that the attribute never existed.

**Verify:** Real DB-backed test — create an `Assignment` with a description via the API, submit code, assert the description text appears in the prompt sent to the mocked provider. (The current test, `test_ai_chat_prompt_content.py`, mocks `.description` directly on a `Mock()` object and would not have caught this — fix or supplement it so it exercises the real model/schema, not just a mock.)

## P0 — `.zip` uploads silently break AI feedback

**Problem:** `async_get_ai_feedback` (`ai_feedback/integration.py`) does `open(file_path, "r").read()` to get code text. A `.zip` upload isn't text — this raises `UnicodeDecodeError`, gets caught by the generic exception handler, and the student sees "AI feedback could not be generated" with no real explanation, on every zip submission.

**Fix (pick one):**
- **Minimal:** detect a non-text/zip file before attempting AI feedback and skip it with an explicit, student-facing message ("AI feedback isn't available for multi-file/zip submissions yet") instead of a generic error. Low risk, ships fast.
- **Better:** extract the entry point file from the zip (instructors likely already specify one for the autograder) and read that for AI context. More useful, more work, touches `routes/submission.py` and `ai_feedback/integration.py`.

**Verify:** New test uploading a `.zip` through `upload_submission` → assert either real feedback or the new explicit message appears, never the current generic decode-failure error.

## P1 — `/ai_chat` ignores instructor `ai_allowed_inputs` toggles

**Problem:** Submission feedback correctly filters context through `build_allowed_feedback_context()`. `/ai_chat` (`routes/code_editor.py`) builds its context inline and always sends description + code, regardless of what the instructor disabled. An instructor who turns off `student_code` or `test_results` for privacy/rubric reasons is only partially protected.

**Fix:** Route `/ai_chat`'s context assembly through `build_allowed_feedback_context()` / `render_feedback_context()` from `ai_feedback/settings.py`, the same functions submission feedback already uses. This also gets `test_results`/`test_cases`/`student_output` support in chat "for free" if that's ever wanted.

**Verify:** Test that disabling `student_code` in `ai_allowed_inputs` results in a chat prompt that does not contain the student's code.

## P1 — `coding_insights` is overwritten, not accumulated

**Problem:** `update_submission_feedback()` does `student.coding_insights = str(new_insights)` — full overwrite every submission. "Past insights" in the next prompt reflect only the most recent AI response, not a real history. This is your own "Future work 2" note, and it's already visibly thin in the current implementation, not just a future risk.

**Fix (scoped, not the full future-memory redesign — see P3 for that):**
- Short-term/low-effort: append instead of overwrite, capped to the last N entries, so at least multiple submissions' worth of signal survives.
- This is a stopgap, not a replacement for the structured-summary design in P3 — flag it as such in the commit/PR so it isn't mistaken for "done."

**Verify:** Submit twice for the same assignment, assert the second submission's prompt contains signal from both the first and second AI responses, not just the second.

## P2 — Test coverage gaps

None of the three P0/P1 items above have regression tests today, and that's exactly how the description bug shipped silently (the existing test mocks around the real bug). Before or alongside each fix above, add:
- Real-DB `Assignment.description` round-trip test (see P0 above).
- `.zip` upload → AI feedback behavior test.
- `/ai_chat` + `ai_allowed_inputs` enforcement test.

## P2 — Repo hygiene: large uncommitted diff against `origin/main`

Not AI-specific, but worth flagging: as of this review, a very large number of files across `backend/` and `frontend/` show as locally modified against `origin/main` in your working copy, unrelated to the AI docs work. Before your next PR, run a quick `git diff <file>` spot-check on a few of these (or compare with a fresh clone) to confirm whether that's real pending work or an environment/line-ending artifact — you don't want it accidentally swept into an unrelated commit via `git add -A`.

## P3 — Real student-history / AI-memory design (your original "Future work 2" list)

This is the bigger, deliberate design work — not a quick patch like the P1 item above. Your own notes already scoped it well:

- **Structured student summaries instead of raw chat history** — e.g. a small structured record per student per assignment (`common_mistake_categories`, `improvement_trend`, `last_n_scores`) generated periodically, rather than a single freeform string. Separate table or JSON column on `users` or a new `student_learning_profile` table.
- **Instructor on/off toggle for memory** — an `ai_memory_enabled` setting (course or assignment level, alongside the existing `ai_allowed_inputs` pattern) so instructors can disable cross-submission personalization where it's not wanted (e.g. exams, integrity-sensitive assignments).
- **Privacy controls for stored history** — retention window, student-visible "what the AI remembers about me" view, and a deletion path (ties into `ai_chat_messages` and whatever new table backs structured summaries).
- **Separate short-term chat context from long-term learning memory** — today these are already somewhat separate (`ai_chat_messages` last-20 vs. `coding_insights`), but `coding_insights` is too thin to count as real long-term memory (see P1). This item is really "build the long-term side properly," with the short-term side already in reasonable shape.

Recommended sequencing: do the P0/P1 items first (they're bug fixes, not redesigns, and the P1 `coding_insights` append-not-overwrite change gives you a safe stopgap). Scope P3 as its own design doc + issue once the immediate gaps are closed, since it touches data model, privacy, and instructor UX in ways that deserve a dedicated review rather than being bundled into a bug-fix PR.
