import io
import os
import shutil
import subprocess
import uuid
import zipfile
import docker
import pytest
from types import SimpleNamespace
from flask import json, session
from api import create_app, db
from api.models import Submission, Assignment, User, SubmissionSubmitter, TestCaseResult, TestCase

import routes.submission as submission_module
from util.errors import ForbiddenError, InternalProcessingError

from routes.submission import submission
# Captured at import time, before the autouse mock below patches the name on
# the routes.submission module — lets us test the real authorization logic
# directly without fighting that fixture.
from routes.submission import _verify_student_owner as real_verify_student_owner

@pytest.fixture
def app():
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        db.create_all()  # Create the tables
        yield app
        db.drop_all()    # Clean up after tests


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(autouse=True)
def mock_verify_student_owner(mocker):
    """Auto-mock session-based auth in submission routes for unit tests."""
    mocker.patch("routes.submission._verify_student_owner")
    mocker.patch("routes.submission._verify_course_staff")


@pytest.fixture
def mock_user_query(mocker):
    """Mock the database query for user lookup."""
    mock_query = mocker.patch("routes.user.db.session.query")
    mock_user_schema = mocker.patch("routes.user.UserSchema")
    return mock_query, mock_user_schema


# Test cases

# Test cases for submission routes


def test_get_submissions_missing_params(client):
    """Test that missing query parameters returns a 400 error."""
    response = client.get("/get_submissions")
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Missing student_id or assignment_id"

def test_get_submissions_not_found(client, mocker):
    """Test /get_submissions returns 404 when no submissions are found."""
    mock_query = mocker.patch("routes.submission.db.session.query")
    mock_query.return_value.filter_by.return_value.all.return_value = []
    
    response = client.get("/get_submissions?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 404
    data = response.get_json()
    assert data["message"] == "No submissions found for the provided student and assignment"


def test_get_submissions_success(client, mocker):
    """Test /get_submissions returns dumped submission data when submissions exist."""
    fake_submissions = [{"id": "sub1", "score": 100}]
    mock_query = mocker.patch("routes.submission.db.session.query")
    mock_query.return_value.filter_by.return_value.all.return_value = fake_submissions

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submissions

    response = client.get("/get_submissions?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == fake_submissions


# Tests for latest submission retrieval


def test_get_latest_submission_missing_params(client):
    """Test that missing parameters in /get_latest_submission returns 400."""
    response = client.get("/get_latest_submission")
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Missing student_id or assignment_id"


def test_get_latest_submission_success(client, mocker):
    """Test /get_latest_submission returns the latest submission data."""
    fake_submission = {"id": "sub1", "score": 100}
    # Patch the query chain for Submission.
    fake_query = mocker.patch.object(Submission, "query", create=True)
    fake_query.filter_by.return_value.order_by.return_value.first.return_value = fake_submission

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submission

    response = client.get("/get_latest_submission?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == fake_submission


def test_get_latest_submission_not_found(client, mocker):
    """Test /get_latest_submission returns a message when no submission is found."""
    fake_query = mocker.patch.object(Submission, "query", create=True)
    fake_query.filter_by.return_value.order_by.return_value.first.return_value = None

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = None

    response = client.get("/get_latest_submission?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == {"message": "No submissions found", "data": None}


# Tests for deleting a submission


def test_delete_submission_missing_id(client):
    """Test /delete_submission returns error when submission_id is missing."""
    response = client.delete("/delete_submission")
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Missing submission_id"


# Tests for activating a submission


def test_activate_submission_missing_params(client):
    """Test /activate_submission returns error if required fields are missing."""
    payload = {"submission_id": "sub1", "student_id": "stu1"}  # missing assignment_id
    response = client.post("/activate_submission", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Missing submission_id, student_id, or assignment_id"


def test_activate_submission_success(client, mocker):
    """Test /activate_submission successfully activates a submission."""
    payload = {"submission_id": "sub1", "student_id": "stu1", "assignment_id": "assgn1"}

    fake_submission = mocker.Mock(student_id="stu1", assignment_id="assgn1")
    mocker.patch("routes.submission.db.session.get", return_value=fake_submission)

    # Patch the query call chain used in the route.
    # Here we simulate that the query returns an object that supports update()
    fake_old_query = mocker.patch("routes.submission.db.session.query")
    fake_old = mocker.Mock()
    fake_old.update.return_value = None
    fake_old_query.return_value.filter_by.return_value = fake_old

    mock_commit = mocker.patch("routes.submission.db.session.commit")

    response = client.post("/activate_submission", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Submission activated successfully"
    mock_commit.assert_called_once()


# Tests for retrieving results


def test_get_results_success(client, mocker):
    """Test /get_results returns submission results for a valid user email."""
    fake_student = mocker.Mock()
    fake_student.id = "stu1"
    fake_submission_data = [{"id": "sub1", "score": 100}]

    # We need to differentiate between the two query calls:
    # one for User and one for Submission.
    def fake_query(model):
        dummy = mocker.Mock()
        if model.__name__ == "User":
            dummy.filter_by.return_value.first.return_value = fake_student
        elif model.__name__ == "Submission":
            dummy.filter_by.return_value.order_by.return_value.limit.return_value = fake_submission_data
        return dummy

    mocker.patch("routes.submission.db.session.query", side_effect=fake_query)

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submission_data

    response = client.get("/get_results?email=test@example.com&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == fake_submission_data


# Tests for testing submission details


def test_get_submission_details_missing_id(client):
    """Test /get_submission_details returns error when submission_id is missing."""
    response = client.get("/get_submission_details")
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Missing submission id"


def test_get_submission_details_success(client, mocker):
    """Test /get_submission_details returns submission details when found."""
    # Mock submission with student_id and assignment_id for _verify_student_owner
    fake_submission = mocker.Mock()
    fake_submission.id = "sub1"
    fake_submission.student_id = "stu1"
    fake_submission.assignment_id = "assgn1"
    fake_submission.score = 100
    fake_submission_dumped = {"id": "sub1", "score": 100}
    dummy_query = mocker.patch("routes.submission.db.session.query")
    dummy_query.return_value.filter_by.return_value.first.return_value = fake_submission

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submission_dumped

    response = client.get("/get_submission_details?submission_id=sub1")
    assert response.status_code == 200
    assert response.get_json() == fake_submission_dumped


def test_rerun_submission_autograder_missing_id(client):
    response = client.post("/rerun_submission_autograder", json={})

    assert response.status_code == 400
    assert response.get_json()["message"] == "Missing submission_id"


def _mock_rerun_submission_and_assignment(mocker, student_id="student-uuid", autograder_image_name=""):
    existing_submission = mocker.Mock()
    existing_submission.id = "sub1"
    existing_submission.assignment_id = "assgn1"
    existing_submission.student_id = student_id

    assignment = mocker.Mock()
    assignment.id = "assgn1"
    assignment.course_id = "course-uuid"
    assignment.autograder_image_name = autograder_image_name

    def fake_get(model, item_id):
        if model.__name__ == "Submission":
            return existing_submission
        if model.__name__ == "Assignment":
            return assignment
        return None

    mocker.patch("routes.submission.db.session.get", side_effect=fake_get)
    return existing_submission, assignment


def test_rerun_submission_autograder_requires_configured_autograder(client, mocker):
    _mock_rerun_submission_and_assignment(mocker, student_id="student-uuid")

    with client.session_transaction() as sess:
        sess["user_id"] = "student-uuid"

    response = client.post(
        "/rerun_submission_autograder",
        json={"submission_id": "sub1"},
    )

    assert response.status_code == 400
    assert "No autograder configured" in response.get_json()["message"]


def test_rerun_submission_autograder_unauthenticated(client, mocker):
    _mock_rerun_submission_and_assignment(mocker)

    response = client.post(
        "/rerun_submission_autograder",
        json={"submission_id": "sub1"},
    )

    assert response.status_code == 401
    assert "Not authenticated" in response.get_json()["message"]


def test_rerun_submission_autograder_forbidden_other_student(client, mocker):
    _mock_rerun_submission_and_assignment(mocker, student_id="owner-uuid")

    with client.session_transaction() as sess:
        sess["user_id"] = "other-student-uuid"

    response = client.post(
        "/rerun_submission_autograder",
        json={"submission_id": "sub1"},
    )

    assert response.status_code == 403
    assert "Not authorized" in response.get_json()["message"]


#  Tests for getting active submission


def test_get_active_submission_success(client, mocker):
    """Test /get_active_submission returns active submission details."""
    fake_submission = {"id": "sub1", "active": True}
    dummy_query = mocker.patch("routes.submission.db.session.query")
    dummy_query.return_value.filter_by.return_value.first.return_value = fake_submission

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submission

    response = client.get("/get_active_submission?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == fake_submission


def test_get_active_submission_not_found(client, mocker):
    """Test /get_active_submission returns message when no active submission exists."""
    dummy_query = mocker.patch("routes.submission.db.session.query")
    dummy_query.return_value.filter_by.return_value.first.return_value = None

    response = client.get("/get_active_submission?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == {"message": "No active submission found", "data": None}


# Edge cases to add in route implementations


def test_upload_submission_missing_file(client):
    """Test /upload_submission returns error when file is missing."""
    # Note: Depending on your app error handling, this might raise an exception.
    response = client.post("/upload_submission", data={})
    # We expect a 400 error for missing file
    assert response.status_code == 400


def _cleanup_submission_dirs(assignment_id):
    """Remove any runs/ and archive/ directories a test created for assignment_id."""
    backend_routes_dir = os.path.dirname(os.path.abspath(submission_module.__file__))
    for subtree in ("runs", "archive"):
        path = os.path.join(backend_routes_dir, "upload_autograder", subtree, assignment_id)
        shutil.rmtree(path, ignore_errors=True)


def _mock_assignment_lookups(mocker, fake_assignment):
    """Mock the Assignment/AssignmentExtension/Submission queries upload_submission makes."""
    def fake_query(model):
        dummy = mocker.Mock()
        if model.__name__ == "Assignment":
            dummy.filter_by.return_value.first.return_value = fake_assignment
        elif model.__name__ == "AssignmentExtension":
            dummy.filter_by.return_value.first.return_value = None
        elif model.__name__ == "Submission":
            dummy.filter_by.return_value.count.return_value = 0
        return dummy

    mocker.patch("routes.submission.db.session.query", side_effect=fake_query)
    mocker.patch("routes.submission.db.session.add")
    mocker.patch("routes.submission.db.session.commit")


def test_upload_submission_no_autograder_archives_staged_files(client, mocker):
    """Test /upload_submission archives the staged files when no autograder is configured."""
    assignment_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    fake_assignment = mocker.Mock()
    fake_assignment.allow_file_upload = True
    fake_assignment.published = True
    fake_assignment.published_date = None
    fake_assignment.due_date = None
    fake_assignment.late_due_date = None
    fake_assignment.late_submission = False
    fake_assignment.autograder_image_name = ""

    _mock_assignment_lookups(mocker, fake_assignment)

    try:
        response = client.post(
            "/upload_submission",
            data={
                "assignment_id": assignment_id,
                "student_id": student_id,
                "file": (io.BytesIO(b"print('hello')"), "solution.py"),
            },
        )

        assert response.status_code == 200
        submission_id = response.get_json()["submissionID"]

        archived_path = submission_module.archive_dir(assignment_id, submission_id)
        assert os.path.isdir(archived_path)
        assert set(os.listdir(archived_path)) == {"solution.py"}

        # The temporary staging directory should be removed.
        staging_dir = os.path.join(
            os.path.dirname(os.path.abspath(submission_module.__file__)),
            "upload_autograder", "runs", assignment_id, "submission", submission_id,
        )
        assert not os.path.exists(staging_dir)
    finally:
        _cleanup_submission_dirs(assignment_id)


def test_upload_submission_success_archives_submission_and_results(client, mocker):
    """Test /upload_submission archives the submission and results after a successful run."""
    assignment_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    fake_assignment = mocker.Mock()
    fake_assignment.allow_file_upload = True
    fake_assignment.published = True
    fake_assignment.published_date = None
    fake_assignment.due_date = None
    fake_assignment.late_due_date = None
    fake_assignment.late_submission = False
    fake_assignment.autograder_image_name = "autograder-test"
    fake_assignment.autograder_timeout = 30

    _mock_assignment_lookups(mocker, fake_assignment)

    fake_container = mocker.Mock()
    fake_container.name = "assignment_container_test"
    mocker.patch("routes.submission.get_or_create_assignment_container", return_value=fake_container)

    # Container cleanup, the autograder run and the results read all go through
    # `docker exec` subprocesses now, so dispatch on the shell command.
    def fake_subprocess_run(args, **kwargs):
        proc = mocker.Mock()
        proc.returncode = 0
        proc.stderr = b""
        command = args[-1] if isinstance(args, (list, tuple)) else ""
        proc.stdout = (
            b'{"score": 100, "execution_time": 1.5}'
            if command.startswith("cat ")
            else b""
        )
        return proc

    mocker.patch("routes.submission.subprocess.run", side_effect=fake_subprocess_run)
    # Without this the route spawns a real async_get_ai_feedback thread against
    # the test database after the response returns. It happens to pass today,
    # but it is a background thread racing test teardown - exactly the shape of
    # a future flake.
    fake_thread = mocker.patch("routes.submission.threading.Thread")

    try:
        response = client.post(
            "/upload_submission",
            data={
                "assignment_id": assignment_id,
                "student_id": student_id,
                "file": (io.BytesIO(b"print('hello')"), "solution.py"),
            },
        )

        assert response.status_code == 200
        assert fake_thread.called
        body = response.get_json()
        submission_id = body["submissionID"]

        archived_path = submission_module.archive_dir(assignment_id, submission_id)
        archived_files = os.listdir(archived_path)
        assert "solution.py" in archived_files
        assert f"results_{submission_id}.json" in archived_files
        assert body["results_path"] == os.path.join(archived_path, f"results_{submission_id}.json")
    finally:
        _cleanup_submission_dirs(assignment_id)


def test_delete_submission_not_found(client, mocker):
    """Test /delete_submission returns 404 when the submission is not found."""
    # Patch the get method to return None.
    # mocker.patch("routes.submission.Submission.query.get", return_value=None)
    mocker.patch(
    "routes.submission.db.session.get",
    return_value=None
)
    with client.session_transaction() as sess:
        sess["user_id"] = "instructor-uuid"

    response = client.delete("/delete_submission?submission_id=123")
    assert response.status_code == 404
    data = response.get_json()
    assert data["message"] == "No submission found to delete"


def test_upload_assignment_autograder_missing_file(client):
    """Test that /upload_assignment_autograder returns an error message when the file is missing."""
    response = client.post("/upload_assignment_autograder", data={})
    assert response.status_code == 400
    data = response.get_json(silent=True)
    
    if data is not None and "error" in data:
        error_message = data["error"]
    else:
        error_message = response.get_data(as_text=True)
    
    assert "No file part" in error_message


def test_delete_submission_success(client, mocker):
    """Test /delete_submission successfully deletes a submission."""
    fake_submission = mocker.Mock(assignment_id="assign-1")
    fake_assignment = mocker.Mock(course_id="course-uuid")

    # Patch the get method on the api.db.session instead of routes.submission.db.session.get
    fake_get = mocker.patch("api.db.session.get", side_effect=[fake_submission, fake_assignment])
    mock_delete = mocker.patch("routes.submission.db.session.delete")
    mock_commit = mocker.patch("routes.submission.db.session.commit")
    mocker.patch("util.auth.get_user_course_role", return_value="instructor")

    with client.session_transaction() as sess:
        sess["user_id"] = "instructor-uuid"

    response = client.delete("/delete_submission?submission_id=123")
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Submission successfully deleted"

    fake_get.assert_any_call(Submission, "123")
    mock_delete.assert_called_once_with(fake_submission)
    mock_commit.assert_called_once()

def test_get_active_submission_missing_params(client):
    response = client.get("/get_active_submission")
    assert response.status_code == 400

    data = response.get_json(silent=True)
    assert data is not None, "Expected a valid JSON response"
    assert data["message"] == "not sufficient details"


# Tests for exporting submissions


def test_export_submissions_missing_assignment_id(client):
    """Test /export_submissions returns 400 when assignment_id is missing."""
    response = client.get("/export_submissions")
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Missing assignment_id"


def test_export_submissions_assignment_not_found(client, mocker):
    """Test /export_submissions returns 404 when the assignment doesn't exist."""
    def query_side_effect(*args, **kwargs):
        mock = mocker.MagicMock()
        if args and args[0] is Assignment:
            mock.filter_by.return_value.first.return_value = None
        return mock

    mocker.patch("routes.submission.db.session.query", side_effect=query_side_effect)

    response = client.get("/export_submissions?assignment_id=assgn1")
    assert response.status_code == 404
    data = response.get_json()
    assert data["message"] == "Assignment not found"


def test_export_submissions_no_active_submissions(client, mocker):
    """Test /export_submissions returns an empty zip with a README when there are no active submissions."""
    fake_assignment = SimpleNamespace(id="assgn1", name="HW1")

    def query_side_effect(*args, **kwargs):
        mock = mocker.MagicMock()
        if args and args[0] is Assignment:
            mock.filter_by.return_value.first.return_value = fake_assignment
        return mock

    mocker.patch("routes.submission.db.session.query", side_effect=query_side_effect)

    mock_submission_query = mocker.patch.object(Submission, "query", create=True)
    mock_submission_query.filter_by.return_value.order_by.return_value.all.return_value = []

    response = client.get("/export_submissions?assignment_id=assgn1")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"

    with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
        assert zf.namelist() == ["README.txt"]
        assert b"No active submissions" in zf.read("README.txt")


def test_export_submissions_success(client, mocker):
    """Test /export_submissions streams back a valid zip with the expected entries."""
    fake_assignment = SimpleNamespace(id="assgn1", name="HW1")
    fake_student = SimpleNamespace(
        id="stu1", name="Jane Doe", email_address="jane@example.com", sis_user_id="jdoe123"
    )
    fake_results = {
        "tests": [{"name": "case 1", "score": 1, "max_score": 1, "status": "passed"}],
        "score": 95.0,
        "execution_time": 1.23,
    }
    fake_ai_feedback = {
        "insights": ["Great job"],
        "annotations": [{"pattern": "print", "comment": "Readable output"}],
    }
    fake_submission = SimpleNamespace(
        id="sub1",
        student_id="stu1",
        assignment_id="assgn1",
        file_name="main.py",
        submission_number=1,
        submitted_at=None,
        student_code_file=b"print('hi')",
        results=json.dumps(fake_results).encode(),
        score=95.0,
        execution_time=1.23,
        active=True,
        completed=True,
        ai_feedback=json.dumps(fake_ai_feedback),
    )

    user_mock = mocker.MagicMock()
    user_mock.filter_by.return_value.first.return_value = fake_student
    user_mock.filter.return_value.all.return_value = [fake_student]

    assignment_mock = mocker.MagicMock()
    assignment_mock.filter_by.return_value.first.return_value = fake_assignment

    submitter_mock = mocker.MagicMock()
    submitter_mock.filter_by.return_value.all.return_value = []

    testcase_join_mock = mocker.MagicMock()
    testcase_join_mock.join.return_value.filter.return_value.all.return_value = []

    def query_side_effect(*args, **kwargs):
        if args and args[0] is Assignment:
            return assignment_mock
        if args and args[0] is User:
            return user_mock
        if args and args[0] is SubmissionSubmitter:
            return submitter_mock
        if args and args[0] is TestCaseResult:
            return testcase_join_mock
        return mocker.MagicMock()

    mocker.patch("routes.submission.db.session.query", side_effect=query_side_effect)

    mock_submission_query = mocker.patch.object(Submission, "query", create=True)
    mock_submission_query.filter_by.return_value.order_by.return_value.all.return_value = [
        fake_submission
    ]

    response = client.get("/export_submissions?assignment_id=assgn1")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"
    assert "attachment" in response.headers["Content-Disposition"]

    with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
        names = zf.namelist()
        assert "jdoe123/main.py" in names
        assert "jdoe123/metadata.json" in names
        assert "jdoe123/results.json" in names
        assert zf.read("jdoe123/main.py") == b"print('hi')"
        assert json.loads(zf.read("jdoe123/results.json")) == fake_results

        metadata = json.loads(zf.read("jdoe123/metadata.json"))
        assert metadata["submission_id"] == "sub1"
        assert metadata["student_sis_user_id"] == "jdoe123"
        assert metadata["score"] == 95.0
        assert metadata["ai_feedback"] == fake_ai_feedback
        assert metadata["autograder_results"] == fake_results
        assert metadata["submitters"] == [
            {
                "id": "stu1",
                "name": "Jane Doe",
                "email": "jane@example.com",
                "sis_user_id": "jdoe123",
            }
        ]
        assert metadata["test_case_results"] == []


def test_get_all_assignment_submissions_missing_assignment_id(client):
    response = client.get("/get_all_assignment_submissions")

    assert response.status_code == 400
    assert response.get_json()["message"] == "Missing assignment_id"

def test_get_all_assignment_submissions_not_found(client, mocker):
    fake_query = mocker.patch.object(Submission, "query", create=True)
    fake_query.filter_by.return_value.order_by.return_value.all.return_value = []

    response = client.get("/get_all_assignment_submissions?assignment_id=assgn1")

    assert response.status_code == 404
    assert response.get_json()["message"] == "No submissions found for this assignment"

def test_get_all_assignment_submissions_success(client, mocker):
    fake_submissions = [{"id": "sub1", "score": 95}]

    fake_query = mocker.patch.object(Submission, "query", create=True)
    fake_query.filter_by.return_value.order_by.return_value.all.return_value = fake_submissions

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submissions

    response = client.get("/get_all_assignment_submissions?assignment_id=assgn1")

    assert response.status_code == 200
    assert response.get_json() == fake_submissions

def test_activate_submission_internal_error(client, mocker):
    payload = {
        "submission_id": "sub1",
        "student_id": "stu1",
        "assignment_id": "assgn1"
    }

    fake_submission = mocker.Mock(student_id="stu1", assignment_id="assgn1")
    mock_session = mocker.patch("routes.submission.db.session")
    mock_session.get.return_value = fake_submission
    mock_session.query.side_effect = Exception("database error")

    response = client.post("/activate_submission", json=payload)

    assert response.status_code == 500
    assert response.get_json()["message"] == "Failed to activate submission"
    mock_session.rollback.assert_called_once()

def test_get_submission_details_not_found(client, mocker):
    mock_query = mocker.patch("routes.submission.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    response = client.get(
        "/get_submission_details?submission_id=sub1"
    )

    assert response.status_code == 404
    assert response.get_json()["message"] == "No submission found"

def test_get_results_user_not_found(client, mocker):
    mock_query = mocker.patch("routes.submission.db.session.query")

    fake_user_query = mocker.Mock()
    fake_user_query.filter_by.return_value.first.return_value = None
    mock_query.return_value = fake_user_query

    response = client.get("/get_results?email=test@test.com&assignment_id=a1")

    assert response.status_code == 404
    assert response.get_json()["message"] == "User not found"


from io import BytesIO

def test_upload_submission_missing_fields(client):
    response = client.post(
        "/upload_submission",
        data={
            "file": (BytesIO(b"hello"), "test.py")
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Missing required fields"

def test_upload_submission_assignment_not_found(client, mocker):
    mock_query = mocker.patch(
        "routes.submission.db.session.query"
    )

    mock_query.return_value.filter_by.return_value.first.return_value = None

    response = client.post(
        "/upload_submission",
        data={
            "assignment_id": "a1",
            "student_id": "s1",
            "file": (BytesIO(b"hello"), "test.py")
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 404

def test_delete_submission_commit_error(client, mocker):
    fake_submission = mocker.Mock(assignment_id="assign-1")
    fake_assignment = mocker.Mock(course_id="course-uuid")

    mocker.patch(
        "routes.submission.db.session.get",
        side_effect=[fake_submission, fake_assignment]
    )
    mocker.patch("util.auth.get_user_course_role", return_value="instructor")

    with client.session_transaction() as sess:
        sess["user_id"] = "instructor-uuid"

    mocker.patch(
        "routes.submission.db.session.delete"
    )

    mocker.patch(
        "routes.submission.db.session.commit",
        side_effect=Exception("db error")
    )

    rollback = mocker.patch(
        "routes.submission.db.session.rollback"
    )

    response = client.delete(
        "/delete_submission?submission_id=123"
    )

    assert response.status_code == 500

    data = response.get_json()
    assert data["message"] == "Failed to delete submission"

    rollback.assert_called_once()


# ---------------------------------------------------------------------------
# Negative-path auth tests (session-based guards)
# ---------------------------------------------------------------------------

def test_delete_submission_unauthenticated(client):
    response = client.delete("/delete_submission?submission_id=123")
    assert response.status_code == 401
    assert "Not authenticated" in response.get_json()["message"]


def test_delete_submission_ta_forbidden(client, mocker):
    fake_submission = mocker.Mock(assignment_id="assign-1")
    fake_assignment = mocker.Mock(course_id="course-uuid")
    mocker.patch("routes.submission.db.session.get", side_effect=[fake_submission, fake_assignment])
    mocker.patch("util.auth.get_user_course_role", return_value="ta")

    with client.session_transaction() as sess:
        sess["user_id"] = "ta-uuid"

    response = client.delete("/delete_submission?submission_id=123")
    assert response.status_code == 403
    assert "Only instructors" in response.get_json()["message"]


def test_upload_assignment_autograder_unauthenticated(client):
    import io
    response = client.post(
        "/upload_assignment_autograder",
        data={"file": (io.BytesIO(b"zip-bytes"), "autograder.zip"), "assignment_id": "assign-1"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 401
    assert "Not authenticated" in response.get_json()["message"]


def test_upload_assignment_autograder_student_forbidden(client, mocker):
    import io
    fake_assignment = mocker.Mock(course_id="course-uuid")
    mock_query = mocker.patch("routes.submission.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = fake_assignment
    mocker.patch("util.auth.get_user_course_role", return_value="student")

    with client.session_transaction() as sess:
        sess["user_id"] = "student-uuid"

    response = client.post(
        "/upload_assignment_autograder",
        data={"file": (io.BytesIO(b"zip-bytes"), "autograder.zip"), "assignment_id": "assign-1"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 403
    assert "Only instructors or TAs" in response.get_json()["message"]


# ---------------------------------------------------------------------------
# Direct tests of the real _verify_student_owner logic (bypasses the
# autouse mock via the reference captured at module import time above).
# ---------------------------------------------------------------------------

def test_verify_student_owner_allows_self(app, mocker):
    mock_user = mocker.Mock(id="stu1")
    mock_query = mocker.patch("routes.submission.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = mock_user

    with app.test_request_context():
        session["user_id"] = "stu1"
        user = real_verify_student_owner("stu1", "assgn1")

    assert user is mock_user


def test_verify_student_owner_denies_other_student(app, mocker):
    mock_assignment = mocker.Mock(course_id="course-1")
    mock_course = mocker.Mock(instructor_id="instructor-uuid")

    def fake_query(model):
        dummy = mocker.Mock()
        if model.__name__ == "Assignment":
            dummy.filter_by.return_value.first.return_value = mock_assignment
        elif model.__name__ == "Course":
            dummy.filter_by.return_value.first.return_value = mock_course
        elif model.__name__ == "Enrollment":
            dummy.filter_by.return_value.first.return_value = None
        return dummy

    mocker.patch("routes.submission.db.session.query", side_effect=fake_query)

    with app.test_request_context():
        session["user_id"] = "other-student-uuid"
        with pytest.raises(ForbiddenError):
            real_verify_student_owner("stu1", "assgn1")


def test_verify_student_owner_allows_enrolled_instructor(app, mocker):
    mock_assignment = mocker.Mock(course_id="course-1")
    mock_course = mocker.Mock(instructor_id="someone-else")
    mock_enrollment = mocker.Mock(role="instructor")
    mock_target_user = mocker.Mock(id="stu1")

    def fake_query(model):
        dummy = mocker.Mock()
        if model.__name__ == "Assignment":
            dummy.filter_by.return_value.first.return_value = mock_assignment
        elif model.__name__ == "Course":
            dummy.filter_by.return_value.first.return_value = mock_course
        elif model.__name__ == "Enrollment":
            dummy.filter_by.return_value.first.return_value = mock_enrollment
        elif model.__name__ == "User":
            dummy.filter_by.return_value.first.return_value = mock_target_user
        return dummy

    mocker.patch("routes.submission.db.session.query", side_effect=fake_query)

    with app.test_request_context():
        session["user_id"] = "instructor-uuid"
        user = real_verify_student_owner("stu1", "assgn1")

    assert user is mock_target_user


def test_verify_student_owner_allows_enrolled_ta(app, mocker):
    mock_assignment = mocker.Mock(course_id="course-1")
    mock_course = mocker.Mock(instructor_id="someone-else")
    mock_enrollment = mocker.Mock(role="ta")
    mock_target_user = mocker.Mock(id="stu1")

    def fake_query(model):
        dummy = mocker.Mock()
        if model.__name__ == "Assignment":
            dummy.filter_by.return_value.first.return_value = mock_assignment
        elif model.__name__ == "Course":
            dummy.filter_by.return_value.first.return_value = mock_course
        elif model.__name__ == "Enrollment":
            dummy.filter_by.return_value.first.return_value = mock_enrollment
        elif model.__name__ == "User":
            dummy.filter_by.return_value.first.return_value = mock_target_user
        return dummy

    mocker.patch("routes.submission.db.session.query", side_effect=fake_query)

    with app.test_request_context():
        session["user_id"] = "ta-uuid"
        user = real_verify_student_owner("stu1", "assgn1")

    assert user is mock_target_user


# ---------------------------------------------------------------------------
# activate_submission: submission must actually belong to the given
# student_id/assignment_id, not just get a caller-authorization pass.
# ---------------------------------------------------------------------------

def test_activate_submission_wrong_student_forbidden(client, mocker):
    fake_submission = mocker.Mock(student_id="owner-uuid", assignment_id="assgn1")
    mocker.patch("routes.submission.db.session.get", return_value=fake_submission)
    mock_commit = mocker.patch("routes.submission.db.session.commit")

    response = client.post("/activate_submission", json={
        "submission_id": "sub1",
        "student_id": "attacker-uuid",
        "assignment_id": "assgn1",
    })

    assert response.status_code == 403
    assert "does not belong" in response.get_json()["message"]
    mock_commit.assert_not_called()


def test_activate_submission_wrong_assignment_forbidden(client, mocker):
    fake_submission = mocker.Mock(student_id="stu1", assignment_id="other-assgn")
    mocker.patch("routes.submission.db.session.get", return_value=fake_submission)
    mock_commit = mocker.patch("routes.submission.db.session.commit")

    response = client.post("/activate_submission", json={
        "submission_id": "sub1",
        "student_id": "stu1",
        "assignment_id": "assgn1",
    })

    assert response.status_code == 403
    assert "does not belong" in response.get_json()["message"]
    mock_commit.assert_not_called()


def test_activate_submission_not_found(client, mocker):
    mocker.patch("routes.submission.db.session.get", return_value=None)

    response = client.post("/activate_submission", json={
        "submission_id": "missing-sub",
        "student_id": "stu1",
        "assignment_id": "assgn1",
    })

    assert response.status_code == 404
    assert response.get_json()["message"] == "No submission found"


def test_exec_run_with_timeout_raises_distinct_timeout(mocker):
    """A wedged helper exec must not look like a student timeout.

    upload_submission treats subprocess.TimeoutExpired as "the student's program
    ran too long" and records a failed submission for it. Container cleanup and
    the results read share the same subprocess mechanism now, so they raise
    ContainerExecTimeout instead to keep the two cases apart.
    """
    container = mocker.Mock()
    container.name = "assignment_container_test"
    mocker.patch(
        "routes.submission.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="docker exec", timeout=30),
    )

    with pytest.raises(submission_module.ContainerExecTimeout):
        submission_module.exec_run_with_timeout(container, "cat /autograder/results/x.json")


def test_exec_run_with_timeout_merges_stdout_and_stderr(mocker):
    """Callers read .output expecting exec_run(demux=False)'s merged stream."""
    container = mocker.Mock()
    container.name = "assignment_container_test"
    proc = mocker.Mock()
    proc.returncode = 1
    proc.stdout = b"out"
    proc.stderr = b"err"
    mocker.patch("routes.submission.subprocess.run", return_value=proc)

    result = submission_module.exec_run_with_timeout(container, "false")

    assert result.exit_code == 1
    assert result.output == b"outerr"


def test_discard_container_lock_removes_entry():
    """_container_locks must not grow for the lifetime of the process."""
    assignment_id = str(uuid.uuid4())
    submission_module.get_container_lock(assignment_id)
    assert assignment_id in submission_module._container_locks

    submission_module.discard_container_lock(assignment_id)
    assert assignment_id not in submission_module._container_locks

    # Discarding an unknown id is a no-op, not a KeyError.
    submission_module.discard_container_lock(assignment_id)


def test_reset_assignment_container_survives_docker_api_error(app, mocker):
    """A daemon error must not swallow the caller's failed-submission record.

    reset_assignment_container runs while the caller is already handling a
    timeout and still has a Submission row to write. If an APIError escaped
    here, the student would get an opaque 500 and no timeout submission at all.
    """
    assignment = mocker.Mock()
    assignment.id = "assign-id"
    assignment.container_id = "container-abc"

    client_mock = mocker.Mock()
    client_mock.containers.get.side_effect = docker.errors.APIError("daemon busy")
    mocker.patch("routes.submission.get_docker_client", return_value=client_mock)
    mocker.patch("routes.submission.db.session.commit")

    submission_module.reset_assignment_container(assignment)

    assert assignment.container_id is None


def test_archive_staged_files_prunes_empty_scaffolding(app):
    """runs/ should be left holding only in-progress work."""
    assignment_id = str(uuid.uuid4())
    submission_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())
    routes_dir = os.path.dirname(os.path.abspath(submission_module.__file__))
    assignment_dir = os.path.join(routes_dir, "upload_autograder", "runs", assignment_id)
    submissions_dir = os.path.join(assignment_dir, "submission", submission_id)
    results_dir = os.path.join(assignment_dir, student_id, "results")

    try:
        os.makedirs(submissions_dir)
        os.makedirs(results_dir)
        with open(os.path.join(submissions_dir, "solution.py"), "w") as f:
            f.write("print('hi')")
        results_path = os.path.join(results_dir, "results.json")
        with open(results_path, "w") as f:
            f.write("{}")

        submission_module.archive_staged_files(
            assignment_id, submission_id, submissions_dir, results_path
        )

        assert not os.path.exists(os.path.join(assignment_dir, "submission"))
        assert not os.path.exists(os.path.join(assignment_dir, student_id))
    finally:
        _cleanup_submission_dirs(assignment_id)


def test_archive_staged_files_keeps_parent_with_concurrent_submission(app):
    """Pruning must never disturb another submission still staging."""
    assignment_id = str(uuid.uuid4())
    mine = str(uuid.uuid4())
    theirs = str(uuid.uuid4())
    routes_dir = os.path.dirname(os.path.abspath(submission_module.__file__))
    assignment_dir = os.path.join(routes_dir, "upload_autograder", "runs", assignment_id)
    my_dir = os.path.join(assignment_dir, "submission", mine)
    their_dir = os.path.join(assignment_dir, "submission", theirs)

    try:
        os.makedirs(my_dir)
        os.makedirs(their_dir)
        with open(os.path.join(my_dir, "solution.py"), "w") as f:
            f.write("print('hi')")

        submission_module.archive_staged_files(assignment_id, mine, my_dir)

        assert os.path.isdir(their_dir)
    finally:
        _cleanup_submission_dirs(assignment_id)


# --- Persistent container isolation, staleness and locking -------------------


def _fake_image(mocker, image_id):
    image = mocker.Mock()
    image.id = image_id
    return image


def test_container_image_is_stale_detects_cache_hit_rebuild(app, mocker):
    """A rebuild that Docker served from cache must still be caught.

    The old check compared image *tags*. It only ever worked because a genuine
    rebuild orphans the old tag, leaving container.image.tags empty. When the
    build context is byte-identical Docker returns the cached image, the tag
    never moves, and a tag comparison sees nothing wrong - so students keep
    grading against the container the instructor thought they had replaced.
    Comparing image IDs is what actually answers the question.
    """
    assignment = mocker.Mock()
    assignment.autograder_image_name = "autograder-1"

    container = mocker.Mock()
    container.image = _fake_image(mocker, "sha256:old")

    client_mock = mocker.Mock()
    client_mock.images.get.return_value = _fake_image(mocker, "sha256:new")
    mocker.patch("routes.submission.get_docker_client", return_value=client_mock)

    assert submission_module._container_image_is_stale(container, assignment) is True

    # Same image ID, and the tag still points at it: nothing to do.
    container.image = _fake_image(mocker, "sha256:new")
    assert submission_module._container_image_is_stale(container, assignment) is False


def test_get_or_create_recreates_container_when_image_changed(app, mocker):
    """The riskiest untested path: rebuild the autograder, next run uses it."""
    assignment = mocker.Mock()
    assignment.id = "assign-1"
    assignment.container_id = "container-old"
    assignment.autograder_image_name = "autograder-1"

    stale_container = mocker.Mock()
    stale_container.id = "container-old"
    stale_container.status = "running"
    stale_container.image = _fake_image(mocker, "sha256:old")

    fresh_container = mocker.Mock()
    fresh_container.id = "container-new"
    fresh_container.status = "running"
    fresh_container.image = _fake_image(mocker, "sha256:new")

    client_mock = mocker.Mock()
    client_mock.containers.get.return_value = stale_container
    client_mock.containers.run.return_value = fresh_container
    client_mock.images.get.return_value = _fake_image(mocker, "sha256:new")
    mocker.patch("routes.submission.get_docker_client", return_value=client_mock)
    mocker.patch("routes.submission.db.session.refresh")
    mocker.patch("routes.submission.db.session.expire")
    mocker.patch("routes.submission.exec_run_with_timeout",
                 return_value=submission_module.ExecResult(0, b""))

    engine_conn = mocker.MagicMock()
    engine = mocker.MagicMock()
    engine.begin.return_value.__enter__.return_value = engine_conn
    mocker.patch("routes.submission._get_engine", return_value=engine)

    result = submission_module.get_or_create_assignment_container(assignment)

    stale_container.remove.assert_called_once()
    assert result is fresh_container
    # container_id is persisted on its own connection, not the caller's session.
    assert engine_conn.execute.called


def test_get_or_create_starts_stopped_container_from_409_path(app, mocker):
    """A 409 hands back a container by name that may well be exited.

    reset_assignment_container can clear container_id without the container
    actually going away, and a daemon restart leaves it exited. The next
    submission then finds container_id NULL, hits 409 on create, fetches the
    stopped container and used to exec straight into it - a 500 for the student
    that only cleared itself on some later request that happened to take the
    other branch.
    """
    assignment = mocker.Mock()
    assignment.id = "assign-1"
    assignment.container_id = None
    assignment.autograder_image_name = "autograder-1"

    stopped_container = mocker.Mock()
    stopped_container.id = "container-existing"
    stopped_container.status = "exited"

    def start_it():
        stopped_container.status = "running"

    stopped_container.start.side_effect = start_it

    client_mock = mocker.Mock()
    client_mock.containers.run.side_effect = docker.errors.APIError(
        "conflict", response=SimpleNamespace(status_code=409)
    )
    client_mock.containers.get.return_value = stopped_container
    mocker.patch("routes.submission.get_docker_client", return_value=client_mock)
    mocker.patch("routes.submission.db.session.refresh")
    mocker.patch("routes.submission.db.session.expire")
    mocker.patch("routes.submission.exec_run_with_timeout",
                 return_value=submission_module.ExecResult(0, b""))

    engine_conn = mocker.MagicMock()
    engine = mocker.MagicMock()
    engine.begin.return_value.__enter__.return_value = engine_conn
    mocker.patch("routes.submission._get_engine", return_value=engine)

    result = submission_module.get_or_create_assignment_container(assignment)

    stopped_container.start.assert_called_once()
    assert result is stopped_container


def test_reset_workspace_removes_dotfiles_and_restores_source(app, mocker):
    """The between-students reset has to cover more than `rm -rf dir/*`.

    A glob skips dotfiles, so a dropped .pth, sitecustomize.py, conftest.py or
    .pytest_cache used to survive into the next student's run. rm -rf also does
    not kill processes, and nothing restored /autograder/source, so a
    submission that wrote to run_autograder or the test files could influence
    every student graded after it on that container.
    """
    container = mocker.Mock()
    exec_mock = mocker.patch(
        "routes.submission.exec_run_with_timeout",
        return_value=submission_module.ExecResult(0, b""),
    )

    submission_module.reset_container_workspace(container)

    script = exec_mock.call_args[0][1]
    assert "find /autograder/submission -mindepth 1 -delete" in script
    assert "find /autograder/results -mindepth 1 -delete" in script
    assert "kill -9 -1" in script
    assert submission_module.SOURCE_BASELINE_PATH in script
    assert "rm -rf /autograder/source" in script


def test_reset_workspace_refuses_to_grade_on_a_dirty_container(app, mocker):
    """A failed reset must fail the request, not grade against leftovers."""
    container = mocker.Mock()
    mocker.patch(
        "routes.submission.exec_run_with_timeout",
        return_value=submission_module.ExecResult(1, b"permission denied"),
    )

    with pytest.raises(InternalProcessingError):
        submission_module.reset_container_workspace(container)


def test_source_baseline_snapshot_is_idempotent(app, mocker):
    """Never re-snapshot: the baseline must come from the pristine image only."""
    container = mocker.Mock()
    assignment = mocker.Mock()
    assignment.id = "assign-1"
    exec_mock = mocker.patch(
        "routes.submission.exec_run_with_timeout",
        return_value=submission_module.ExecResult(0, b""),
    )

    submission_module._snapshot_autograder_source(container, assignment)

    script = exec_mock.call_args[0][1]
    assert script.startswith(f"test -d {submission_module.SOURCE_BASELINE_PATH} ||")


def test_advisory_lock_key_is_stable_across_processes():
    """hash() is randomised per process; the lock key must not be.

    Two gunicorn workers deriving different keys for the same assignment would
    take different advisory locks and grade concurrently in one container,
    which is the whole failure this lock exists to prevent.
    """
    assignment_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    key = submission_module._advisory_lock_key(assignment_id)

    assert key == submission_module._advisory_lock_key(assignment_id)
    assert key != submission_module._advisory_lock_key(str(uuid.uuid4()))
    # Must fit Postgres bigint.
    assert -(2 ** 63) <= key < 2 ** 63


def test_assignment_container_lock_takes_and_releases_advisory_lock(app, mocker):
    """On Postgres the lock has to span processes, not just threads."""
    conn = mocker.MagicMock()
    engine = mocker.MagicMock()
    engine.dialect.name = "postgresql"
    engine.connect.return_value = conn
    mocker.patch("routes.submission._get_engine", return_value=engine)

    assignment_id = str(uuid.uuid4())
    with submission_module.assignment_container_lock(assignment_id):
        pass

    statements = [call.args[0] for call in conn.exec_driver_sql.call_args_list]
    assert any("pg_advisory_lock" in s for s in statements)
    assert any("pg_advisory_unlock" in s for s in statements)
    conn.close.assert_called_once()


def test_assignment_container_lock_releases_on_exception(app, mocker):
    """A failed grading run must not leave the advisory lock held."""
    conn = mocker.MagicMock()
    engine = mocker.MagicMock()
    engine.dialect.name = "postgresql"
    engine.connect.return_value = conn
    mocker.patch("routes.submission._get_engine", return_value=engine)

    with pytest.raises(RuntimeError):
        with submission_module.assignment_container_lock(str(uuid.uuid4())):
            raise RuntimeError("autograder exploded")

    statements = [call.args[0] for call in conn.exec_driver_sql.call_args_list]
    assert any("pg_advisory_unlock" in s for s in statements)
    conn.close.assert_called_once()


def test_assignment_container_lock_skips_advisory_on_sqlite(app, mocker):
    """sqlite has no advisory locks; the in-process lock stands alone there."""
    engine = mocker.MagicMock()
    engine.dialect.name = "sqlite"
    mocker.patch("routes.submission._get_engine", return_value=engine)

    with submission_module.assignment_container_lock(str(uuid.uuid4())):
        pass

    engine.connect.assert_not_called()


def test_reset_assignment_container_survives_commit_failure(app, mocker):
    """The docstring promises this never raises - including from its finally.

    On a timeout the caller runs this and then records the student's failed
    submission. A commit error escaping here replaced that record with a bare
    500 and lost the row entirely, which is the outcome the swallow-and-log
    contract exists to prevent.
    """
    assignment = mocker.Mock()
    assignment.id = "assign-id"
    assignment.container_id = "container-abc"

    client_mock = mocker.Mock()
    client_mock.containers.get.return_value = mocker.Mock()
    mocker.patch("routes.submission.get_docker_client", return_value=client_mock)
    mocker.patch("routes.submission.db.session.commit",
                 side_effect=Exception("database is gone"))
    rollback = mocker.patch("routes.submission.db.session.rollback")

    submission_module.reset_assignment_container(assignment)

    assert assignment.container_id is None
    rollback.assert_called_once()


def test_upload_submission_records_row_for_malformed_results(client, mocker):
    """Unusable autograder output must still leave the student a record.

    json.loads(...)['score'] used to raise straight out of the Submission
    constructor: a bare 500, no submission row, and the finally deleting the
    staged code, so the attempt left no trace anyone could look at.
    """
    assignment_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    fake_assignment = mocker.Mock()
    fake_assignment.allow_file_upload = True
    fake_assignment.published = True
    fake_assignment.published_date = None
    fake_assignment.due_date = None
    fake_assignment.late_due_date = None
    fake_assignment.late_submission = False
    fake_assignment.autograder_image_name = "autograder-test"
    fake_assignment.autograder_timeout = 30

    _mock_assignment_lookups(mocker, fake_assignment)

    fake_container = mocker.Mock()
    fake_container.name = "assignment_container_test"
    mocker.patch("routes.submission.get_or_create_assignment_container", return_value=fake_container)
    mocker.patch("routes.submission.threading.Thread")

    def fake_subprocess_run(args, **kwargs):
        proc = mocker.Mock()
        proc.returncode = 0
        proc.stderr = b""
        command = args[-1] if isinstance(args, (list, tuple)) else ""
        # Valid JSON, but no `score` key - the KeyError half of the finding.
        proc.stdout = b'{"tests": []}' if command.startswith("cat ") else b""
        return proc

    mocker.patch("routes.submission.subprocess.run", side_effect=fake_subprocess_run)
    recorded = mocker.patch("routes.submission._record_failed_submission")

    try:
        response = client.post(
            "/upload_submission",
            data={
                "assignment_id": assignment_id,
                "student_id": student_id,
                "file": (io.BytesIO(b"print('hello')"), "solution.py"),
            },
        )

        assert response.status_code == 500
        assert recorded.called
        # The staged code is archived rather than dropped on the floor.
        kwargs = recorded.call_args.kwargs
        assert kwargs["assignment_id"] == assignment_id
        assert kwargs["results"]["score"] == 0
    finally:
        _cleanup_submission_dirs(assignment_id)


def test_upload_submission_discards_container_on_autograder_failure(client, mocker):
    """A non-zero autograder exit must tear the shared container down.

    The run went off the rails somewhere we cannot see, and anything the
    submission spawned is still alive in there. The old per-submission
    container was destroyed on every exit path; leaving this one running hands
    the next student someone else's processes.
    """
    assignment_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    fake_assignment = mocker.Mock()
    fake_assignment.allow_file_upload = True
    fake_assignment.published = True
    fake_assignment.published_date = None
    fake_assignment.due_date = None
    fake_assignment.late_due_date = None
    fake_assignment.late_submission = False
    fake_assignment.autograder_image_name = "autograder-test"
    fake_assignment.autograder_timeout = 30

    _mock_assignment_lookups(mocker, fake_assignment)

    fake_container = mocker.Mock()
    fake_container.name = "assignment_container_test"
    mocker.patch("routes.submission.get_or_create_assignment_container", return_value=fake_container)

    def fake_subprocess_run(args, **kwargs):
        proc = mocker.Mock()
        command = args[-1] if isinstance(args, (list, tuple)) else ""
        proc.returncode = 0 if command.startswith(("test ", "\n", "kill")) else 1
        proc.stdout = b""
        proc.stderr = b"Traceback ..."
        return proc

    mocker.patch("routes.submission.subprocess.run", side_effect=fake_subprocess_run)
    mocker.patch("routes.submission.reset_container_workspace")
    reset = mocker.patch("routes.submission.reset_assignment_container")

    try:
        response = client.post(
            "/upload_submission",
            data={
                "assignment_id": assignment_id,
                "student_id": student_id,
                "file": (io.BytesIO(b"print('hello')"), "solution.py"),
            },
        )

        assert response.status_code == 500
        reset.assert_called_once()
    finally:
        _cleanup_submission_dirs(assignment_id)
