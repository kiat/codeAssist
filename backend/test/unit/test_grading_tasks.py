import json
import os
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from api import create_app, db
from api.models import (
    Assignment, Submission,
    SUBMISSION_PENDING, SUBMISSION_RUNNING, SUBMISSION_GRADED, SUBMISSION_FAILED,
)
from util.errors import InternalProcessingError
import routes.submission as submission_module
import routes.grading_tasks as grading_tasks


@pytest.fixture
def app():
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def grading(mocker):
    container = mocker.Mock()
    container.name = "assignment_container_test"
    mocker.patch("routes.submission.get_or_create_assignment_container", return_value=container)

    def set_exit(returncode, stdout=b"", stderr=b""):
        return mocker.patch(
            "routes.submission.run_grading",
            return_value=SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr),
        )

    return SimpleNamespace(
        set_exit=set_exit,
        reset=mocker.patch("routes.submission.reset_assignment_container"),
        thread=mocker.patch("routes.grading_tasks.threading.Thread"),
    )


def _assignment(timeout=30):
    assignment = Assignment(
        id=str(uuid.uuid4()), name="A1", course_id=str(uuid.uuid4()),
        allow_file_upload=True, published=True,
        autograder_image_name="autograder-test", autograder_timeout=timeout,
    )
    db.session.add(assignment)
    db.session.commit()
    return assignment.id


def _submission(assignment_id, student_id=None, status=SUBMISSION_PENDING,
                active=False, submitted_at=None, stage=True):
    sub = Submission(
        id=str(uuid.uuid4()), file_name="solution.py",
        student_id=student_id or str(uuid.uuid4()), assignment_id=assignment_id,
        student_code_file=b"print('hello')", results=None, score=None,
        execution_time=0.0, submitted_at=submitted_at or datetime.now(),
        active=active, completed=False, status=status, submission_number=1,
    )
    db.session.add(sub)
    db.session.commit()
    if stage:
        staged = submission_module.staging_dir(assignment_id, sub.id)
        os.makedirs(staged, exist_ok=True)
        with open(os.path.join(staged, "solution.py"), "wb") as f:
            f.write(b"print('hello')")
    return sub.id


def _run(submission_id):
    grading_tasks.grade_submission.run(submission_id)
    db.session.expire_all()
    return db.session.get(Submission, submission_id)


def _cleanup(assignment_id):
    routes_dir = os.path.dirname(os.path.abspath(submission_module.__file__))
    for subtree in ("runs", "archive"):
        shutil.rmtree(os.path.join(routes_dir, "upload_autograder", subtree, assignment_id), ignore_errors=True)


@pytest.fixture
def assignment_id(app):
    assignment_id = _assignment()
    yield assignment_id
    _cleanup(assignment_id)


def test_grade_submission_records_clean_grade_and_activates(assignment_id, grading):
    submission_id = _submission(assignment_id)
    grading.set_exit(0, stdout=b'{"score": 100, "execution_time": 1.5}')

    sub = _run(submission_id)

    assert sub.status == SUBMISSION_GRADED
    assert sub.score == 100
    assert sub.execution_time == 1.5
    assert sub.completed is True
    assert sub.active is True
    assert sub.grading_started_at is not None
    archived = os.listdir(submission_module.archive_dir(assignment_id, submission_id))
    assert set(archived) == {"solution.py", f"results_{submission_id}.json"}
    assert not os.path.exists(submission_module.staging_dir(assignment_id, submission_id))
    assert grading.thread.called


def test_grade_submission_logs_step_timings(assignment_id, grading, caplog):
    caplog.set_level("INFO", logger="routes.grading_tasks")
    submission_id = _submission(assignment_id)
    grading.set_exit(0, stdout=b'{"score": 100}')

    _run(submission_id)

    logged = [r.getMessage() for r in caplog.records if r.getMessage().startswith("grading_timing")]
    assert len(logged) == 1
    timings = json.loads(logged[0].split(" ", 3)[3])
    expected_steps = {
        "stage", "prepare", "lock_wait", "container", "grade", "record", "total",
    }
    assert set(timings) == expected_steps
    assert all(value >= 0 for value in timings.values())
    steps_sum = sum(value for name, value in timings.items() if name != "total")
    assert steps_sum <= timings["total"] + 0.001


def test_grade_submission_records_timeout_when_autograder_runs_too_long(assignment_id, grading):
    submission_id = _submission(assignment_id)
    grading.set_exit(submission_module.GRADE_EXIT_TIMED_OUT)

    sub = _run(submission_id)

    assert sub.status == SUBMISSION_GRADED
    assert sub.score == 0
    assert sub.completed is False
    assert sub.active is True
    grading.reset.assert_called_once()
    results = json.loads(sub.results)
    assert results["tests"][0]["name"] == "Submission Timeout"
    assert sub.execution_time == 30.0
    assert os.path.isdir(submission_module.archive_dir(assignment_id, submission_id))
    assert not grading.thread.called


@pytest.mark.parametrize("returncode", [
    submission_module.GRADE_EXIT_AUTOGRADER_FAILED,
    137,  # killed, e.g. out of memory
])
def test_grade_submission_discards_container_on_autograder_failure(assignment_id, grading, returncode):
    """A non-zero autograder exit must tear the shared container down."""
    submission_id = _submission(assignment_id)
    grading.set_exit(returncode, stderr=b"Traceback ...")

    sub = _run(submission_id)

    grading.reset.assert_called_once()

    # The attempt is recorded and archived rather than vanishing.
    assert sub.status == SUBMISSION_GRADED
    assert sub.score == 0
    results = json.loads(sub.results)
    assert results["tests"][0]["name"] == "Autograder Error"
    # stderr stays in the server log, never in what the student sees.
    assert "Traceback" not in json.dumps(results)
    assert os.path.isdir(submission_module.archive_dir(assignment_id, submission_id))


def test_grade_submission_records_attempt_when_results_json_missing(assignment_id, grading):
    """Missing results.json is recorded but keeps the container."""
    submission_id = _submission(assignment_id)
    grading.set_exit(
        submission_module.GRADE_EXIT_NO_RESULTS,
        stderr=b"cat: /autograder/results/results.json: No such file or directory",
    )

    sub = _run(submission_id)

    # Only a hung exec means the container is suspect; a missing file does not.
    grading.reset.assert_not_called()
    assert sub.status == SUBMISSION_GRADED
    assert sub.score == 0
    # The container path from cat's error is not shown to the student.
    assert "/autograder/results" not in sub.results.decode()


@pytest.mark.parametrize("returncode", [
    submission_module.GRADE_EXIT_RESET_FAILED,
    submission_module.GRADE_EXIT_COPY_FAILED,
    125,  # docker failed to run the exec
    126,
    127,
    2,
])
def test_grade_submission_marks_infra_failure_failed_and_keeps_previous_active(assignment_id, grading, returncode):
    """Setup failed before student code ran: discard container, mark the row failed."""
    student_id = str(uuid.uuid4())
    previous_id = _submission(
        assignment_id, student_id, status=SUBMISSION_GRADED, active=True,
        submitted_at=datetime.now() - timedelta(hours=1), stage=False,
    )
    submission_id = _submission(assignment_id, student_id)
    grading.set_exit(returncode, stderr=b"permission denied")

    sub = _run(submission_id)

    assert sub.status == SUBMISSION_FAILED
    assert sub.active is False
    assert sub.score is None
    grading.reset.assert_called_once()
    assert db.session.get(Submission, previous_id).active is True
    assert not grading.thread.called


def test_grade_submission_records_timeout_when_grading_exec_hangs(assignment_id, grading, mocker, caplog):
    submission_id = _submission(assignment_id)
    mocker.patch(
        "routes.submission.run_grading",
        side_effect=submission_module.ContainerExecTimeout("stuck"),
    )

    sub = _run(submission_id)

    grading.reset.assert_called_once()
    assert json.loads(sub.results)["tests"][0]["name"] == "Submission Timeout"
    assert os.path.isdir(submission_module.archive_dir(assignment_id, submission_id))
    assert any("safety timeout" in r.getMessage() for r in caplog.records if r.levelname == "WARNING")


@pytest.mark.parametrize("stored_timeout", [None, 0])
def test_grade_submission_defaults_missing_timeout_to_300(app, grading, stored_timeout):
    assignment_id = _assignment(timeout=stored_timeout)
    submission_id = _submission(assignment_id)
    run = grading.set_exit(submission_module.GRADE_EXIT_TIMED_OUT)

    try:
        sub = _run(submission_id)

        assert run.call_args.args[3] == 300
        assert sub.execution_time == 300.0
    finally:
        _cleanup(assignment_id)


@pytest.mark.parametrize("stdout", [
    b'{"tests": []}',
    b'\xff\xfe{"score": 1}',
    b'[1, 2, 3]',
])
def test_grade_submission_records_attempt_for_unusable_results(assignment_id, grading, stdout):
    submission_id = _submission(assignment_id)
    grading.set_exit(0, stdout=stdout)

    sub = _run(submission_id)

    assert sub.status == SUBMISSION_GRADED
    assert sub.score == 0
    assert sub.completed is False
    assert json.loads(sub.results)["tests"][0]["name"] == "Autograder Error"
    assert os.path.isdir(submission_module.archive_dir(assignment_id, submission_id))
    assert not grading.thread.called


def test_grade_submission_releases_db_connection_before_waiting_for_lock(assignment_id, grading, mocker):
    """Waiting submissions must not pin a pooled connection for the whole wait."""
    submission_id = _submission(assignment_id)
    seen = []

    @submission_module.contextmanager
    def fake_lock(lock_id):
        seen.append((lock_id, db.session().in_transaction()))
        raise InternalProcessingError("stop after lock")
        yield

    mocker.patch("routes.submission.assignment_container_lock", side_effect=fake_lock)

    sub = _run(submission_id)

    assert seen == [(assignment_id, False)]
    assert sub.status == SUBMISSION_FAILED


def test_grade_submission_skips_deleted_submission(app, grading):
    run = grading.set_exit(0, stdout=b'{"score": 1}')

    grading_tasks.grade_submission.run(str(uuid.uuid4()))

    run.assert_not_called()


@pytest.mark.parametrize("status", [SUBMISSION_GRADED, SUBMISSION_FAILED])
def test_grade_submission_skips_finished_submission(assignment_id, grading, status):
    submission_id = _submission(assignment_id, status=status, stage=False)
    run = grading.set_exit(0, stdout=b'{"score": 1}')

    sub = _run(submission_id)

    run.assert_not_called()
    assert sub.status == status


def test_grade_submission_skips_submission_already_running(assignment_id, grading):
    # A redelivered message must not grade a row another worker has claimed.
    submission_id = _submission(assignment_id, status=SUBMISSION_RUNNING)
    run = grading.set_exit(0, stdout=b'{"score": 5}')

    sub = _run(submission_id)

    run.assert_not_called()
    grading.thread.assert_not_called()
    assert sub.status == SUBMISSION_RUNNING
    assert sub.score is None


def test_grade_submission_retries_when_claim_commit_fails(assignment_id, grading, mocker):
    from celery.exceptions import Retry
    submission_id = _submission(assignment_id)
    run = grading.set_exit(0, stdout=b'{"score": 5}')
    retry = mocker.patch.object(grading_tasks.grade_submission, "retry", side_effect=Retry())
    mocker.patch.object(db.session, "commit", side_effect=RuntimeError("db down"))

    with pytest.raises(Retry):
        grading_tasks.grade_submission.run(submission_id)

    mocker.stopall()
    db.session.rollback()
    run.assert_not_called()
    assert retry.call_args.kwargs["countdown"] == grading_tasks.CLAIM_RETRY_COUNTDOWN_SECONDS
    assert retry.call_args.kwargs["max_retries"] == grading_tasks.CLAIM_MAX_RETRIES
    assert db.session.get(Submission, submission_id).status == SUBMISSION_PENDING



def test_grade_submission_fails_row_when_claim_retries_run_out(assignment_id, grading, mocker):
    submission_id = _submission(assignment_id)
    run = grading.set_exit(0, stdout=b'{"score": 5}')
    retry = mocker.patch.object(grading_tasks.grade_submission, "retry")
    real_commit = db.session.commit
    calls = {"n": 0}

    def commit_fails_once():
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("db down")
        return real_commit()

    mocker.patch.object(db.session, "commit", side_effect=commit_fails_once)

    grading_tasks.grade_submission.push_request(retries=grading_tasks.CLAIM_MAX_RETRIES)
    try:
        grading_tasks.grade_submission.run(submission_id)
    finally:
        grading_tasks.grade_submission.pop_request()

    mocker.stopall()
    db.session.expire_all()
    run.assert_not_called()
    retry.assert_not_called()
    assert db.session.get(Submission, submission_id).status == SUBMISSION_FAILED
    assert not _staged(assignment_id, submission_id)

def _staged(assignment_id, submission_id):
    return os.path.isdir(submission_module.staging_dir(assignment_id, submission_id))


def test_unclaimed_message_keeps_files_another_worker_is_grading(assignment_id, grading):
    submission_id = _submission(assignment_id, status=SUBMISSION_RUNNING)
    grading.set_exit(0, stdout=b'{"score": 5}')

    _run(submission_id)

    assert _staged(assignment_id, submission_id)


def test_unclaimed_message_archives_files_of_a_swept_submission(assignment_id, grading):
    submission_id = _submission(assignment_id, status=SUBMISSION_FAILED)
    grading.set_exit(0, stdout=b'{"score": 5}')

    _run(submission_id)

    assert not _staged(assignment_id, submission_id)
    assert os.listdir(submission_module.archive_dir(assignment_id, submission_id)) == ["solution.py"]


def test_unclaimed_message_removes_files_of_a_deleted_submission(assignment_id, grading):
    submission_id = _submission(assignment_id)
    db.session.query(Submission).filter_by(id=submission_id).delete()
    db.session.commit()
    grading.set_exit(0, stdout=b'{"score": 5}')

    _run(submission_id)

    assert not _staged(assignment_id, submission_id)
    assert not os.path.exists(submission_module.archive_dir(assignment_id, submission_id))


def _change_row_during_grading(mocker, submission_id, **fields):
    """run_grading stub that changes the row mid-grade, as the sweep plus a
    staff rerun would, then returns a score of 5."""
    def grade(*args, **kwargs):
        db.session.query(Submission).filter_by(id=submission_id).update(fields, synchronize_session=False)
        db.session.commit()
        return SimpleNamespace(returncode=0, stdout=b'{"score": 5}', stderr=b"")
    return mocker.patch("routes.submission.run_grading", side_effect=grade)


def test_late_result_does_not_overwrite_a_rerun(assignment_id, grading, mocker):
    submission_id = _submission(assignment_id)
    _change_row_during_grading(mocker, submission_id, status=SUBMISSION_GRADED, score=42)

    sub = _run(submission_id)

    assert sub.status == SUBMISSION_GRADED
    assert sub.score == 42
    grading.thread.assert_not_called()
    assert not _staged(assignment_id, submission_id)


def test_late_result_still_records_on_a_swept_row(assignment_id, grading, mocker):
    submission_id = _submission(assignment_id)
    _change_row_during_grading(mocker, submission_id, status=SUBMISSION_FAILED)

    sub = _run(submission_id)

    assert sub.status == SUBMISSION_GRADED
    assert sub.score == 5


def _sweep(app, running_seconds=3600, pending_seconds=7200):
    app.config["GRADING_STUCK_RUNNING_SECONDS"] = running_seconds
    app.config["GRADING_STUCK_PENDING_SECONDS"] = pending_seconds
    count = grading_tasks.sweep_stuck_submissions.run()
    db.session.expire_all()
    return count


def _set(submission_id, **fields):
    db.session.query(Submission).filter_by(id=submission_id).update(fields)
    db.session.commit()


def test_sweep_fails_old_running_and_pending_rows(app, assignment_id):
    now = datetime.now(timezone.utc)
    old_running = _submission(assignment_id, status=SUBMISSION_RUNNING, stage=False)
    _set(old_running, grading_started_at=now - timedelta(hours=2))
    old_pending = _submission(assignment_id, status=SUBMISSION_PENDING, stage=False,
                              submitted_at=now - timedelta(hours=3))

    assert _sweep(app) == 2

    assert db.session.get(Submission, old_running).status == SUBMISSION_FAILED
    assert db.session.get(Submission, old_pending).status == SUBMISSION_FAILED


def test_sweep_leaves_recent_and_finished_rows_alone(app, assignment_id):
    now = datetime.now(timezone.utc)
    running = _submission(assignment_id, status=SUBMISSION_RUNNING, stage=False)
    _set(running, grading_started_at=now - timedelta(minutes=10))
    # Queued for over an hour, but under the pending limit (deadline burst).
    pending = _submission(assignment_id, status=SUBMISSION_PENDING, stage=False,
                          submitted_at=now - timedelta(minutes=90))
    graded = _submission(assignment_id, status=SUBMISSION_GRADED, stage=False,
                         submitted_at=now - timedelta(days=3))

    assert _sweep(app) == 0

    assert db.session.get(Submission, running).status == SUBMISSION_RUNNING
    assert db.session.get(Submission, pending).status == SUBMISSION_PENDING
    assert db.session.get(Submission, graded).status == SUBMISSION_GRADED


def test_sweep_uses_submitted_at_for_running_row_without_start_time(app, assignment_id):
    old = _submission(assignment_id, status=SUBMISSION_RUNNING, stage=False,
                      submitted_at=datetime.now(timezone.utc) - timedelta(hours=2))

    assert _sweep(app) == 1

    assert db.session.get(Submission, old).status == SUBMISSION_FAILED


def test_swept_submission_can_be_rerun_later_but_not_regraded_by_late_message(app, assignment_id, grading):
    old = _submission(assignment_id, status=SUBMISSION_PENDING,
                      submitted_at=datetime.now(timezone.utc) - timedelta(hours=3))
    run = grading.set_exit(0, stdout=b'{"score": 5}')
    _sweep(app)

    sub = _run(old)

    run.assert_not_called()
    assert sub.status == SUBMISSION_FAILED


def test_beat_schedules_the_sweep(app):
    schedule = app.config["CELERY"]["beat_schedule"]
    assert any(entry["task"] == "grading.sweep_stuck_submissions" for entry in schedule.values())


def test_grade_submission_rebuilds_missing_staged_file_from_row(assignment_id, grading, mocker):
    submission_id = _submission(assignment_id, stage=False)
    seen = {}

    def fake_run_grading(container, file_path, filename, timeout):
        with open(file_path, "rb") as f:
            seen["content"] = f.read()
        return SimpleNamespace(returncode=0, stdout=b'{"score": 1}', stderr=b"")

    mocker.patch("routes.submission.run_grading", side_effect=fake_run_grading)

    sub = _run(submission_id)

    assert seen["content"] == b"print('hello')"
    assert sub.status == SUBMISSION_GRADED


def test_grade_submission_marks_failed_on_unexpected_error(assignment_id, grading, mocker):
    submission_id = _submission(assignment_id)
    mocker.patch("routes.submission.run_grading", side_effect=RuntimeError("docker daemon gone"))

    sub = _run(submission_id)

    assert sub.status == SUBMISSION_FAILED
    assert sub.active is False


def test_grade_submission_handles_submission_deleted_during_grading(assignment_id, grading, mocker):
    submission_id = _submission(assignment_id)

    def delete_then_grade(container, file_path, filename, timeout):
        db.session.query(Submission).filter_by(id=submission_id).delete()
        db.session.commit()
        return SimpleNamespace(returncode=0, stdout=b'{"score": 1}', stderr=b"")

    mocker.patch("routes.submission.run_grading", side_effect=delete_then_grade)

    grading_tasks.grade_submission.run(submission_id)

    assert db.session.get(Submission, submission_id) is None
    assert os.listdir(submission_module.archive_dir(assignment_id, submission_id)) == ["solution.py"]
    assert not grading.thread.called


def test_grade_submission_archives_files_when_final_commit_fails(assignment_id, grading, mocker):
    submission_id = _submission(assignment_id)
    grading.set_exit(0, stdout=b'{"score": 1}')
    real_commit_or_rollback = grading_tasks.commit_or_rollback

    def fail_final_commit(reason, *args, raise_message=None):
        if reason.startswith("Failed to record submission"):
            raise InternalProcessingError(raise_message)
        return real_commit_or_rollback(reason, *args, raise_message=raise_message)

    mocker.patch("routes.grading_tasks.commit_or_rollback", side_effect=fail_final_commit)

    sub = _run(submission_id)

    assert sub.status == SUBMISSION_FAILED
    archived = os.listdir(submission_module.archive_dir(assignment_id, submission_id))
    assert "solution.py" in archived
    assert not os.path.exists(submission_module.staging_dir(assignment_id, submission_id))


def test_grade_submission_leaves_late_finisher_inactive(assignment_id, grading):
    student_id = str(uuid.uuid4())
    now = datetime.now()
    newer_id = _submission(assignment_id, student_id, status=SUBMISSION_GRADED,
                           active=True, submitted_at=now, stage=False)
    older_id = _submission(assignment_id, student_id, submitted_at=now - timedelta(minutes=1))
    grading.set_exit(0, stdout=b'{"score": 3}')

    older = _run(older_id)

    assert older.status == SUBMISSION_GRADED
    assert older.active is False
    assert db.session.get(Submission, newer_id).active is True


def test_submission_deleted_right_after_claim_is_skipped_and_cleaned_up(assignment_id, grading, mocker):
    submission_id = _submission(assignment_id)
    run = grading.set_exit(0, stdout=b'{"score": 5}')
    real_get = db.session.get

    def deleted_after_claim(model, ident, *args, **kwargs):
        if model is Submission and str(ident) == str(submission_id):
            db.session.query(Submission).filter_by(id=submission_id).delete()
            db.session.commit()
            return None
        return real_get(model, ident, *args, **kwargs)

    mocker.patch.object(db.session, "get", side_effect=deleted_after_claim)

    grading_tasks.grade_submission.run(submission_id)

    run.assert_not_called()
    assert not _staged(assignment_id, submission_id)
