# Publish Grades — Design Document

## Context

The Review Grades page (`frontend/src/pages/reviewGrades/index.js`) already shipped CSV download and Export Submissions (PRs #358/#359). The last unbuilt item from issue #243's original punch list is **Publish Grades**. A tracking PR (#373) exists for it, but it is an empty draft — zero files changed — pointing back to issues **#243** and **#277** as the actual spec. This document is the result of reading both issues' comment threads, auditing the current codebase end-to-end, and working through the product/architecture decisions before any code is written.

**Note on PR #373's body:** it states it replaces PR #362 because #362's branch "was force-pushed by an unauthorized actor" and GitHub wouldn't allow reopening it. That claim comes from PR/issue text — external, unverified data — and is being surfaced here for awareness, not acted upon. It is unrelated to the feature design below and would need separate follow-up (credential/access review) if not already resolved.

This document is a design reference for whoever implements the feature. No code has been written yet.

---

## Current state (verified in codebase, not assumed)

- **No grade-visibility concept exists anywhere.** Grep across backend + frontend for `release`, `visible`, `hide_grade`, `is_visible`, `show_to_student`, `grade_visible`, `grade_release` returns nothing. Students see `Submission.score` the instant it's set.
- **`Assignment.published` / `Assignment.published_date` already exist** (`backend/api/models.py:64-65`) but mean "is the assignment open for submission" — checked in `submission.py:192` and `code_editor.py:270,791`. This name is **already taken** for an unrelated concept; any new field must not collide with it, and future readers must not confuse the two.
- **`Submission` has no status/visibility/graded-at field at all** (`backend/api/models.py:90-107`). Grading state is inferred from `score is not None` / `completed`.
- **The "Publish Grades" button already exists in the UI** (`frontend/src/pages/reviewGrades/index.js`, ~line 245) with no `onClick` handler — a dead placeholder, same pattern as the also-dead "Export Evaluations" button and the unwired "EMAIL NOTIFICATION" checkbox in the roster add-user modals. This is a known pattern in this codebase (UI shipped ahead of backend).
- **No email/notification infrastructure exists** — no SMTP, Flask-Mail, or SendGrid anywhere in the backend.
- **Student-facing grade reads happen through three routes**, all gated by `_verify_student_owner()` (`backend/routes/submission.py:68`), which allows *either* the owning student *or* course staff through, then dump the full `SubmissionSchema` (every column, unconditionally) regardless of caller identity:
  - `get_submission_details` (`submission.py:733`) — the one actually used by the student result page (`frontend/src/pages/result/index.js`, `TestResultsDisplay.js`), via `GET /get_submission_details?submission_id=...`.
  - `get_latest_submission` (`submission.py:506`)
  - `get_results` (`submission.py:478`, docstring says "instructor side view" but uses the same owner-or-staff check, so a student session can also reach it)
  - Instructor-only routes (`get_all_assignment_submissions`, `export_submissions`, `export_grades_csv`) are gated by `_verify_course_staff` and are **not** in scope for redaction — instructors/TAs always see everything regardless of publish state.
- **Roles are plain strings** (`"student"`, `"instructor"`, `"ta"`), checked via `require_course_role(course_id, allowed_roles, message)` in `backend/util/auth.py:40`. No decorators, no `"admin"` enrollment role.
- **`regrade_request.py`'s `send_regrade_request` has no auth check at all today** (pre-existing gap, unrelated to this feature — noted so it isn't mistaken for something this design introduces).
- Assignment creation/update routes: `create_assignment` (`backend/routes/assignment.py:127`) and `update_assignment` (`backend/routes/assignment.py:34`). Frontend create form: `frontend/src/pages/instructor/assignments/CreateAssignment.js`. Edit/settings form: `frontend/src/pages/assignmentSettings/index.js` (per `CLAUDE.md`).
- Student-facing assignment list with a score column: `frontend/src/pages/assignments/index.js`.

---

## Decisions (each with the "why," since some are non-obvious)

1. **Design from issues #243/#277, not from PR #373/#362** — neither PR has usable code; #362's file list was the entire repo, not a real diff.
2. **Publish is whole-assignment only, not per-student.** Simplest model; matches the primary Gradescope flow the issue comments reference. This means **no schema change to `Submission` is needed at all** — the entire feature lives on `Assignment`.
3. **Default is immediate visibility; holding is opt-in per assignment.** Follows the explicit product comment on #243 ("there should be an *option* to hold the results") rather than an inference. Also zero-risk: no backfill needed, existing assignments are unaffected.
4. **Publish gates the score and autograder/test-case output, not AI feedback.** Hiding score while leaving test-case pass/fail counts visible would let a student trivially back-compute the grade, so both must move together. AI feedback is explicitly left ungated: `CLAUDE.md` flags the AI feedback pipeline (`async_get_ai_feedback` + the separate inline `/ai_chat` context-building in `code_editor.py`) as split across two paths with a known inconsistency "not an oversight to fix casually." Threading a new gate through both paths is out of scope for a feature the issue text describes as "publish *grades*," not "publish feedback." This is a **documented known gap**, not an oversight — same pattern `docs/ai/README.md` already uses for its own gaps.
5. **Un-publish is allowed** — the same flag toggles back off, so an instructor who finds a mistake after publishing can hide grades again before correcting and re-publishing.
6. **Instructors and TAs can both publish/unpublish.** Matches the existing pattern where grading actions (e.g. `update_grade` in `regrade_request.py:89`) already use `require_course_role(..., {"instructor", "ta"})`.
7. **`hold_grades` is locked at assignment creation — not editable afterward.** The alternative (editable in assignment settings any time) was explicitly considered and rejected: because visibility is `(not hold_grades) or grades_published`, editing `hold_grades` after some submissions are already graded either (a) makes currently-visible grades vanish with no confirmation step, or (b) makes currently-hidden grades appear as a side effect of a settings-form save rather than a deliberate Publish click — both undermine the feature's own premise. Locking it at creation avoids needing to invent and test either mitigation. Known limitation, accepted deliberately: an instructor who forgets to set it at creation has no way to turn on holding retroactively for that assignment (the only workaround is the existing per-submission `delete_submission`/`activate_submission` tools, which are blunt instruments, not equivalent).
8. **Students see an explicit "pending publish" indicator, not a silent blank score.** Requires touching the student-facing assignment list (`frontend/src/pages/assignments/index.js`) in addition to the individual result page, so a held grade doesn't look like a bug or lost submission.
9. **"Compose email" (issue #243's stretch goal) is out of scope for this design**, flagged as a follow-up. No email infrastructure exists in the backend today; choosing an SMTP/provider and building deliverability is a separate infrastructure decision that shouldn't be bundled into the publish-grades schema/endpoint work.
10. **Doc location: `docs/features/`.** None of the existing `docs/` subdirectories fit — `docs/ai/` is AI-specific, `docs/endpoints/` is REST reference style, `docs/ai/proposals` is AI-only historical designs. This starts a general non-AI feature-design convention.

---

## Data model design

Add three columns to `Assignment` (`backend/api/models.py`, near the existing `published`/`published_date` fields — with an inline comment distinguishing them, since the names are easy to confuse):

```python
hold_grades = db.Column(db.Boolean, nullable=False, default=False)
grades_published = db.Column(db.Boolean, nullable=False, default=False)
grades_published_at = db.Column(TIMESTAMP(timezone=True), nullable=True)
```

- `hold_grades` — set once, at creation, via `create_assignment`. Never accepted by `update_assignment` (explicit enforcement point for decision #7 — either omit it from the accepted-fields list or reject the request if the caller tries to change it).
- `grades_published` — toggled by the new publish/unpublish action. Only meaningful when `hold_grades=True`; irrelevant (visibility already true) when `hold_grades=False`.
- `grades_published_at` — set to `utcnow()` on publish, cleared to `None` on unpublish. Used for display ("Published on Aug 25, 2026") and as a lightweight audit trail.

Add a computed property on the `Assignment` model to centralize the visibility rule in one place (reused by every gated route):

```python
@property
def grades_visible_to_students(self):
    return (not self.hold_grades) or self.grades_published
```

**Migration:** new file in `backend/migrations/versions/`, generated via `flask db migrate -m "add grade publish fields to assignment"`, then hand-reviewed per `CLAUDE.md`'s migration guidance. Server defaults (`False`/`False`/`NULL`) mean every existing assignment is automatically and correctly backfilled to "immediate visibility, nothing held" — no manual data migration. Before committing the migration, run `flask db heads` to confirm a single head (this chain has needed manual head-merging before).

No changes to `Submission` or `backend/api/schemas.py`'s `SubmissionSchema` structure — redaction happens by mutating the dumped dict per-request (see below), matching the codebase's existing manual/explicit style rather than introducing marshmallow context wiring.

---

## Backend changes

**`backend/routes/submission.py`** — modify three existing routes to redact `score` and the test-case/results field when the caller is the student themselves (not staff) and `not assignment.grades_visible_to_students`:

- `get_submission_details` (line 733) — primary path, used by the student result page.
- `get_latest_submission` (line 506)
- `get_results` (line 478)

Pattern for each: after `_verify_student_owner`, determine staff-vs-student the same way `rerun_submission_autograder` already does (`get_user_course_role(requester_id, assignment.course_id) in {"instructor", "ta"}`, `submission.py:776`). If not staff and not visible, strip `score` and the results/test-case field from the dumped dict and add `"grades_published": False` to the response payload so the frontend can render the pending state deliberately rather than inferring it from missing fields.

New route:

```
POST /publish_grades
body: { assignment_id, published: bool }
auth: require_course_role(assignment.course_id, {"instructor", "ta"}, "Only instructors or TAs can publish grades")
```

Sets `assignment.grades_published = published` and `grades_published_at = utcnow() if published else None`.

**`backend/routes/assignment.py`**:
- `create_assignment` (line 127) — accept optional `hold_grades` in the request body, default `False`.
- `update_assignment` (line 34) — explicitly does **not** accept changes to `hold_grades` (enforcement of decision #7).

**Required implementation-time audit (not yet fully enumerated here):** `get_active_submission` (`submission.py:951`) and any other route that serializes a `Submission` and is reachable by a student session must be individually checked before implementation is considered complete — the three routes above are the ones confirmed reachable by a student via `_verify_student_owner`, but this list should be treated as a starting checklist, not a guaranteed-complete one. Grep for every call site of `SubmissionSchema(...).dump(...)` and classify each by caller (staff-only vs. student-reachable) before shipping.

---

## Frontend changes

- **`frontend/src/pages/reviewGrades/index.js`** — wire the existing dead "Publish Grades" button (~line 245): on click, open a confirmation modal (new file, e.g. `frontend/src/pages/reviewGrades/PublishGradesModal.js`, mirroring the existing `ExportSubmissions.js` modal pattern) confirming the action and student count, then call a new `publishGrades(assignmentId, published)` service function (in `frontend/src/services/submission.js`) hitting `POST /publish_grades`. Button should only be shown/enabled when the assignment has `hold_grades=true`, and its label should toggle between "Publish Grades" / "Unpublish Grades" based on current `grades_published` state.
- **`frontend/src/pages/instructor/assignments/CreateAssignment.js`** — add a "Hold grades until published" checkbox wired to `hold_grades`, sent only on the create request.
- **`frontend/src/pages/assignmentSettings/index.js`** — deliberately does **not** expose `hold_grades` as editable (enforces decision #7 on the frontend too, in addition to the backend rejecting it).
- **`frontend/src/pages/result/index.js`** and **`TestResultsDisplay.js`** — when the API response carries `grades_published: false`, render a "Your grade is being finalized and hasn't been published yet" state instead of a blank/null score and test results.
- **`frontend/src/pages/assignments/index.js`** — the student-facing assignment list; when a submission is graded but not yet visible, show a "Grade pending" status in place of the score (decision #8).

---

## Explicitly out of scope (documented gaps, not oversights)

- **AI feedback / AI chat visibility** — not gated by publish state (decision #4). Risk: a student could infer correctness from AI feedback text even with the score hidden. Recorded here so it isn't rediscovered as a surprise later.
- **Compose email / notify-on-publish** — no infrastructure exists; needs its own design (SMTP/provider choice) before it can be scoped (decision #9).
- **Per-student selective publish** — whole-assignment only (decision #2).
- **`hold_grades` editability after creation** — permanently out of scope as designed; would need the mitigation logic discussed in decision #7 if ever revisited.
- **`regrade_request.py`'s missing auth check** — pre-existing, unrelated bug, not introduced or fixed by this design; flagged so it isn't conflated with this feature's own auth model.
- **PR #373's "unauthorized actor force-pushed #362's branch" claim** — unverified external text, not investigated as part of this design; flagged for separate follow-up if not already resolved.

---

## Testing plan

- **Backend** (`backend/test/unit/test_submission.py`, `backend/test/unit/test_assignment.py` — both already exist):
  - Student cannot see `score`/results pre-publish when `hold_grades=True` and `grades_published=False`.
  - Student sees score immediately when `hold_grades=False` (regression guard for current/default behavior).
  - Staff (instructor and TA) always see full data regardless of publish state.
  - `POST /publish_grades` requires `{instructor, ta}` role; rejects student callers.
  - Publishing sets `grades_published_at`; unpublishing clears it.
  - `update_assignment` rejects/ignores attempts to change `hold_grades` after creation.
  - Migration: `flask db heads` remains a single head after the new migration is added.
- **Frontend** (`frontend/src/test/unit/pages/reviewGrades/`, `frontend/src/test/unit/pages/result/`, `frontend/src/test/unit/pages/instructor/assignments/CreateAssignment.test.jsx`):
  - Publish Grades button wiring and confirmation modal.
  - Result page renders the "pending" state on `grades_published: false`.
  - CreateAssignment form submits `hold_grades` correctly; assignment settings form does not expose it.

---

## Residual risks / things to double-check before implementation starts

- The "audit every `Submission`-serializing route" step above is a real gap in this document, not a formality — it was not fully completed here and should not be treated as done.
- `get_results`' docstring says "instructor side view" but its auth check (`_verify_student_owner`) is identical to the two confirmed student-reachable routes — worth confirming with a live request/test whether any student-facing frontend code actually calls it, or whether it's dead from the student side (affects whether redacting it is necessary or just precautionary).
- The naming collision risk between `Assignment.published` (submission window) and the new `Assignment.grades_published` (grade visibility) is real; a future reviewer skimming a diff could easily assume they're related or duplicate. Recommend an explicit code comment at both fields pointing at each other's different purpose.
- This document reflects a design discussion, not a verified-correct implementation — several details (exact field name for test-case results in `SubmissionSchema`, whether `frontend/src/services/submission.js` uses named exports or a different pattern, whether `frontend/src/pages/assignments/index.js` is used by students only or also by instructors in a shared component) should be re-confirmed by whoever implements this, not assumed from this document alone.
