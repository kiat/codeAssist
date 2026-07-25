# AI Feedback — Improvement Roadmap

Prioritized plan based on the code review in `README.md`/`architecture.md`. Each item lists the problem, the fix, the files involved, and how to verify it. P0 = correctness/trust gap affecting every submission today; P1 = real inconsistency worth fixing before it compounds; P2 = test-debt and hardening; P3 = longer-term design work (this is where your "Future work 2: student history / AI memory" notes belong).

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
