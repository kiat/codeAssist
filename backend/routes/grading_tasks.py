import glob
import json
import logging
import os
import shutil
import threading
from datetime import datetime, timedelta, timezone

from celery import shared_task
from flask import current_app
from sqlalchemy import and_, func, or_

from api import db
from api.models import (
    Assignment, Submission,
    SUBMISSION_PENDING, SUBMISSION_RUNNING, SUBMISSION_GRADED, SUBMISSION_FAILED,
)
from ai_feedback.integration import async_get_ai_feedback
from util.timing import StepTimer
from routes.submission import (
    GRADE_OUTCOME_GRADED, GRADE_OUTCOME_INFRA_ERROR,
    grade_staged_submission, activate_if_newest, archive_staged_files,
    commit_or_rollback, staging_dir, results_staging_path, _failed_outcome_payload,
)

logger = logging.getLogger(__name__)

# A claim fails when the database is unreachable, e.g. Postgres still starting.
# Retrying puts a fresh copy of the message on the queue; acks_late alone would
# ack the original as soon as the task returns or raises.
CLAIM_RETRY_COUNTDOWN_SECONDS = 15
CLAIM_MAX_RETRIES = 5

# Rows a finished worker may still write its result to. "failed" is included so
# a job that outlived the sweep still records its real result, unless a rerun
# has already replaced it with "graded".
_RECORDABLE_STATUSES = (SUBMISSION_RUNNING, SUBMISSION_FAILED)


@shared_task(bind=True, name="grading.grade_submission")
def grade_submission(self, submission_id):
    # Claim the row in one UPDATE so a redelivered copy of this message can't
    # also grade it. Only pending rows are claimed; a row left running by a
    # crashed worker is failed by sweep_stuck_submissions instead.
    try:
        claimed = db.session.query(Submission).filter(
            Submission.id == submission_id,
            Submission.status == SUBMISSION_PENDING,
        ).update(
            {"status": SUBMISSION_RUNNING, "grading_started_at": datetime.now(timezone.utc)},
            synchronize_session=False,
        )
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        if self.request.retries >= CLAIM_MAX_RETRIES:
            # Out of retries: fail the row now so the student can see it and
            # rerun, instead of waiting for the pending sweep.
            logger.exception(
                "Failed to claim submission %s after %d retries; marking it failed",
                submission_id, CLAIM_MAX_RETRIES,
            )
            _mark_failed(submission_id)
            _clean_up_unclaimed(submission_id)
            return
        logger.warning("Failed to claim submission %s; retrying", submission_id, exc_info=True)
        raise self.retry(exc=exc, countdown=CLAIM_RETRY_COUNTDOWN_SECONDS, max_retries=CLAIM_MAX_RETRIES)

    if not claimed:
        logger.info("Submission %s is missing or not pending; skipping grading", submission_id)
        _clean_up_unclaimed(submission_id)
        return

    submission = db.session.get(Submission, submission_id)
    if submission is None:
        # Deleted between the claim and this read.
        logger.info("Submission %s was deleted right after it was claimed; skipping grading", submission_id)
        _clean_up_unclaimed(submission_id)
        return
    assignment_id = submission.assignment_id
    filename = submission.file_name
    submissions_dir = staging_dir(assignment_id, submission_id)
    file_path = os.path.join(submissions_dir, filename)

    timer = StepTimer()
    try:
        if not os.path.isfile(file_path):
            os.makedirs(submissions_dir, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(submission.student_code_file)
        timer.lap("stage")

        assignment = db.session.get(Assignment, assignment_id)
        outcome = grade_staged_submission(assignment, file_path, filename, timer)
        _record_outcome(submission_id, assignment_id, outcome, submissions_dir)
        timer.lap("record")
    except Exception:
        logger.exception("Grading crashed for submission %s", submission_id)
        _mark_failed(submission_id)
    finally:
        logger.info(
            "grading_timing assignment=%s submission=%s %s",
            assignment_id, submission_id, json.dumps(timer.as_dict())
        )


def _clean_up_unclaimed(submission_id):
    """Remove the staged upload for a message that claimed nothing, unless
    another worker is grading the row right now and still needs it."""
    try:
        row = db.session.query(Submission.assignment_id, Submission.status).filter_by(id=submission_id).first()
    except Exception:
        db.session.rollback()
        logger.exception("Could not look up unclaimed submission %s; leaving its files", submission_id)
        return

    if row is None:
        # Deleted: the row is gone, so drop the copy too.
        for path in glob.glob(staging_dir("*", submission_id)):
            shutil.rmtree(path, ignore_errors=True)
        return
    if row.status in (SUBMISSION_PENDING, SUBMISSION_RUNNING):
        return
    # Swept or already finished: keep the code with the submission's archive,
    # like every other finished submission.
    submissions_dir = staging_dir(row.assignment_id, submission_id)
    if os.path.isdir(submissions_dir):
        archive_staged_files(row.assignment_id, submission_id, submissions_dir)


def _record_outcome(submission_id, assignment_id, outcome, submissions_dir):
    # Lock the row and re-check it: the sweep or a staff rerun may have changed
    # it while this job was grading. Taking the row lock before
    # activate_if_newest's student lock matches the rerun route's order.
    submission = (
        db.session.query(Submission)
        .filter(Submission.id == submission_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if submission is None:
        db.session.rollback()
        logger.info("Submission %s was deleted during grading; discarding result", submission_id)
        archive_staged_files(assignment_id, submission_id, submissions_dir)
        return
    if submission.status not in _RECORDABLE_STATUSES:
        db.session.rollback()
        logger.warning(
            "Submission %s is %s, likely rerun after the sweep; discarding this late result",
            submission_id, submission.status,
        )
        archive_staged_files(assignment_id, submission_id, submissions_dir)
        return

    student_id = submission.student_id
    filename = submission.file_name

    if outcome.kind == GRADE_OUTCOME_INFRA_ERROR:
        submission.status = SUBMISSION_FAILED
        commit_or_rollback("Failed to mark submission %s failed", submission_id)
        archive_staged_files(assignment_id, submission_id, submissions_dir)
        return

    results_file_path = None
    if outcome.kind == GRADE_OUTCOME_GRADED:
        results_json_content = outcome.results_json_content
        submission.results = results_json_content.encode()
        submission.score = outcome.score
        submission.execution_time = outcome.execution_time
        submission.completed = True

        results_file_path = results_staging_path(assignment_id, student_id, submission_id)
        os.makedirs(os.path.dirname(results_file_path), exist_ok=True)
        with open(results_file_path, "w") as f:
            f.write(results_json_content)
    else:
        results, execution_time = _failed_outcome_payload(outcome)
        submission.results = json.dumps(results).encode()
        submission.score = 0
        submission.execution_time = float(execution_time)
        submission.completed = False

    submission.status = SUBMISSION_GRADED

    activated = activate_if_newest(submission)
    try:
        commit_or_rollback(
            "Failed to record submission %s for assignment %s",
            submission_id, assignment_id,
            raise_message="Failed to record submission"
        )
    except Exception:
        archive_staged_files(assignment_id, submission_id, submissions_dir, results_file_path)
        raise
    if not activated:
        logger.info(
            "Submission %s finished after a newer submission was already active; left inactive",
            submission_id
        )

    archived = archive_staged_files(assignment_id, submission_id, submissions_dir, results_file_path)

    if outcome.kind == GRADE_OUTCOME_GRADED:
        threading.Thread(
            target=async_get_ai_feedback,
            args=(current_app._get_current_object(), submission_id, os.path.join(archived, filename), results_json_content)
        ).start()


@shared_task(name="grading.sweep_stuck_submissions")
def sweep_stuck_submissions():
    """Mark submissions that have been pending or running for too long as failed,
    so they can be rerun. Covers a failed claim commit, a failed `_mark_failed`
    commit, a crashed worker, and a message lost from Redis. Run by Celery beat."""
    now = datetime.now(timezone.utc)
    running_cutoff = now - timedelta(seconds=current_app.config["GRADING_STUCK_RUNNING_SECONDS"])
    pending_cutoff = now - timedelta(seconds=current_app.config["GRADING_STUCK_PENDING_SECONDS"])

    stuck = db.session.query(Submission).filter(or_(
        and_(
            Submission.status == SUBMISSION_RUNNING,
            func.coalesce(Submission.grading_started_at, Submission.submitted_at) < running_cutoff,
        ),
        and_(
            Submission.status == SUBMISSION_PENDING,
            Submission.submitted_at < pending_cutoff,
        ),
    ))
    stuck_ids = [row.id for row in stuck.with_entities(Submission.id)]
    if not stuck_ids:
        return 0

    try:
        stuck.update({"status": SUBMISSION_FAILED}, synchronize_session=False)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Stuck-submission sweep failed to update %d rows", len(stuck_ids))
        raise

    logger.warning("Marked %d stuck submissions failed: %s", len(stuck_ids), stuck_ids)
    return len(stuck_ids)


def _mark_failed(submission_id):
    try:
        db.session.rollback()
        db.session.query(Submission).filter(
            Submission.id == submission_id,
            Submission.status.in_((SUBMISSION_PENDING, SUBMISSION_RUNNING)),
        ).update({"status": SUBMISSION_FAILED}, synchronize_session=False)
        db.session.commit()
    except Exception:
        logger.exception("Could not mark submission %s failed; it stays running", submission_id)
        db.session.rollback()
