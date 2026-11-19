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

This does not make grading faster. One assignment still has one container,
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
   10 minutes.

## Decisions

1. **Async only, no container pool yet.** The assignment lock moves into the
   worker. Different assignments grade in parallel (concurrency 2); one
   assignment still grades one at a time.
2. **Queue: Celery + Redis**, with `task_acks_late`, `task_reject_on_worker_lost`
   and `worker_prefetch_multiplier=1` so a job whose worker crashes before
   claiming it is redelivered instead of lost. The alternative was a Postgres queue (no new services, but a
   hand-written worker loop).
3. **The submission row is the source of truth.** `status` is `pending`,
   `running`, `graded` (student code ran, including score-0 timeouts and
   crashes) or `failed` (our fault). The UI never reads Redis.
4. **Jobs are safe to run twice.** The worker claims a row with one
   `UPDATE ... SET status='running' WHERE id=:id AND status='pending'` and skips
   the job if no row changed, so a redelivered copy can't grade the same
   submission again or start a second AI feedback run.
5. **A sweep fails rows that stay non-terminal.** Celery beat runs
   `grading.sweep_stuck_submissions` every 5 minutes. It marks `running` rows
   older than `GRADING_STUCK_RUNNING_SECONDS` (default 1 hour, measured from
   `grading_started_at`) and `pending` rows older than
   `GRADING_STUCK_PENDING_SECONDS` (default 2 hours, from `submitted_at`) as
   `failed`, so they can be rerun. This covers a failed claim or
   `_mark_failed` commit, a worker that crashed mid-grade (its redelivered job
   finds the row `running` and skips it), and a message lost from Redis. The
   pending limit is long on purpose: a deadline burst on one assignment
   queues behind a single container. If a worker finishes a row after the
   sweep failed it, the real result still overwrites `failed`.
6. **Only `graded` rows become active, and the newest upload wins**, decided
   under an advisory lock on (student, assignment). The previous active
   submission keeps counting until then.
7. **If enqueueing fails**, the pending row is deleted and the student is asked
   to try again.
8. **Rerun and activate return 409** for a submission that isn't graded yet.

## Data Model

```text
submissions
+ status              pending | running | graded | failed   (backfill: graded, CHECK constraint)
+ grading_started_at  nullable; when grading started, read by the stuck-row sweep
```

## Deployment

- `redis`: `redis:7.4-alpine`, no published port, AOF persistence, 64MB cap
  with `noeviction`.
- `worker`: backend image running `celery -A make_celery worker --concurrency=2`,
  with the same env, the same `docker.sock` mount, and the same `./backend/`
  volume, so it sees files Flask stages under `upload_autograder/runs/`.
- `beat`: backend image running `celery -A make_celery beat`, which schedules
  the stuck-row sweep. Run exactly one. Its schedule file is written to `/tmp`,
  not the bind mount.
- The VM deployment needs the same three services before this can ship.
