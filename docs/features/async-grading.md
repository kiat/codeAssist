> **Implemented** for issue #148 in PR #TODO.

# Async Grading

## Goal

`upload_submission` stops holding the request open while grading runs. It
stores the submission, enqueues a grading job, and returns right away. A
background worker grades it, and the frontend polls for the result.

Before this, the request waited in `assignment_container_lock` for the whole
grade. During a deadline burst, most server time was spent waiting on that lock.
Those waiting requests tied up backend threads that every other page also
needs, and they hit nginx's 300s timeout.

This does **not** make grading faster. One assignment still has one container,
so a burst still grades about 1.9 submissions/s. A container pool is a separate
follow-up.

## Flow

1. Student uploads. Flask validates as before, stages the file, inserts a
   `pending` submission row, commits, enqueues `grade_submission(id)`, and
   returns **202** `{submissionID, status}`.
2. A Celery worker (`routes/grading_tasks.py`) claims the row (`running`), takes
   the existing assignment lock, and runs `grade_staged_submission`, which wraps
   the unchanged `run_grading`.
3. The worker records the result (`graded` or `failed`), updates `active`
   (see Decisions), archives, and starts AI feedback in a background thread, as
   before.
4. The results page polls `GET /get_submission_status` every 2s until the
   status is final, then loads the full submission once. It stops polling after
   20 minutes.

## Decisions

1. **Async only, no container pool yet.** `assignment_container_lock` moves from
   the request into the worker. With worker concurrency 2, different assignments
   grade in parallel, and one assignment still grades one at a time.
2. **Queue: Celery + Redis.** It's standard, and retries and worker processes
   come built in. The alternative is a Postgres queue (`FOR UPDATE SKIP LOCKED`
   on pending rows): no new services, but we'd write the worker loop and crash
   recovery ourselves. Required settings, tested in `test_app_config.py`:
   `task_acks_late=True`, `task_reject_on_worker_lost=True`,
   `worker_prefetch_multiplier=1`, and `imports` including
   `routes.grading_tasks`. Redis has no published port. Its 2-hour
   `visibility_timeout` only controls how fast a lost job is retried, never
   whether a submission is graded twice (see 4).
3. **The submission row is the source of truth.** The UI never reads Redis. A
   new `status` column tracks the row:
   - `pending`: stored, not claimed yet.
   - `running`: a worker claimed it.
   - `graded`: student code ran. Covers exit 0 and the score-0 cases
     92/93/94/137, as before.
   - `failed`: our fault (90, 91, 125–127, unexpected, or the worker crashed).
     Replaces the old "500, no row".

   `completed` keeps its old meaning, since the frontend reads it.
4. **Jobs are safe to run twice.** Celery delivers at least once. The task
   grades a row that is `pending` or `running` and skips one that is `graded`,
   `failed`, or deleted. There is no "stale claim" time check: a killed worker's
   job is redelivered immediately, and a stale check would make that redelivery
   skip the row and leave it `running` forever. The cost is that a duplicate
   delivery during a grade longer than the visibility timeout grades twice,
   which is harmless (same result, same activation).
5. **Only `graded` rows become active, and the newest upload wins.** The previous
   active submission keeps counting in stats, the gradebook, and exports until
   the new one is graded. A finishing row becomes active only if its
   `submitted_at` (now set at upload time) is newer than the current active
   row's. This happens in one transaction under an advisory lock on
   (student, assignment), which `activate_submission` and the pending insert
   also take. Nothing is deleted. Only the `active` flag moves.
6. **A failed enqueue removes the row.** If Redis is unreachable, the pending row
   is deleted and the student gets "Grading is temporarily unavailable, please
   try again." No row is left stuck at `pending`, and no submission number is
   used up.
7. **No acting on a submission mid-grade.** Rerunning a `pending` or `running`
   submission returns 409, and so does activating a submission that isn't
   `graded`.

## Data Model

```text
submissions
+ status              pending | running | graded | failed   (backfill: graded, CHECK constraint)
+ grading_started_at  nullable; when grading started, for a future stuck-row sweeper
```

## Deployment

- `redis`: `redis:7.4-alpine`, no published port, AOF persistence, 64MB cap
  with `noeviction`.
- `worker`: backend image running `celery -A make_celery worker --concurrency=2`,
  with the same env, the same `docker.sock` mount, and the same `./backend/`
  volume, so it sees files Flask stages under `upload_autograder/runs/`.
- The VM deployment needs the same two services before this can ship.

## Open Questions

- Celery is the proposed queue; needs sign-off from Kia/Dario.
- If Redis loses a job, its row stays `pending`. Should a periodic sweeper
  re-enqueue old pending rows, and fail old `running` ones?
- Auto-retry `failed` jobs, or let the student resubmit?
- `activate_submission` lets a student choose an older submission. Should a
  newer pending one override that choice when it finishes? (Today it does.)
- If an instructor re-uploads the autograder while jobs are queued, should
  those jobs grade against the new autograder?
- Should `rerun_submission_autograder`, `test_autograder_submission`, and the code
  editor's `submit_code` move to the queue?
- Should there be a per-student cap on pending jobs?
- Move AI feedback to its own Celery queue so it can never hold a grading slot?
- Add an upper bound on `autograder_timeout`?
- Show a "grading…" badge on the assignments list?
- The results page's AI-feedback poll never stops on score-0 rows, which never
  get AI feedback (existing behavior).
