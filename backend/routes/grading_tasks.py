import json
import logging
import os
import threading
from datetime import datetime, timezone

from celery import shared_task
from flask import current_app

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


@shared_task(name="grading.grade_submission")
def grade_submission(submission_id):
    submission = db.session.get(Submission, submission_id)

    if submission is None:
        logger.info("Submission %s no longer exists; skipping grading", submission_id)
        return

    if submission.status not in (SUBMISSION_PENDING, SUBMISSION_RUNNING):
        return

    submission.status = SUBMISSION_RUNNING
    submission.grading_started_at = datetime.now(timezone.utc)
    commit_or_rollback("Failed to claim submission %s", submission_id, raise_message="Failed to claim submission")

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


def _record_outcome(submission_id, assignment_id, outcome, submissions_dir):
    submission = db.session.get(Submission, submission_id)
    if submission is None:
        logger.info("Submission %s was deleted during grading; discarding result", submission_id)
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
