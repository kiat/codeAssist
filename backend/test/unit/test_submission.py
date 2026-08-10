import os
import io
import zipfile
import pytest
from types import SimpleNamespace
from flask import json, session
from api import create_app, db
from api.models import Submission, Assignment, User, SubmissionSubmitter, TestCaseResult, TestCase
from util.errors import ForbiddenError

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
    fake_submission = SimpleNamespace(
        id="sub1",
        student_id="stu1",
        assignment_id="assgn1",
        file_name="main.py",
        submission_number=1,
        submitted_at=None,
        student_code_file=b"print('hi')",
        results=None,
        score=95.0,
        execution_time=1.23,
        active=True,
        completed=True,
        ai_feedback="Great job",
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

        metadata = json.loads(zf.read("jdoe123/metadata.json"))
        assert metadata["submission_id"] == "sub1"
        assert metadata["score"] == 95.0
        assert metadata["ai_feedback"] == "Great job"
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
