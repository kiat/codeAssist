import os
import io
import csv
import uuid
import zipfile
import pytest
from datetime import datetime, timedelta, timezone
from flask import json
from api import create_app, db
from api.models import Assignment, Course, Enrollment, Submission, User


from routes.submission import submission

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
    mock_model = mocker.patch.object(Submission, "query", create=True)
    mock_model.filter_by.return_value.order_by.return_value.first.return_value = fake_submission

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submission

    response = client.get("/get_latest_submission?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == fake_submission


def test_get_latest_submission_not_found(client, mocker):
    """Test /get_latest_submission returns a message when no submission is found."""
    mock_model = mocker.patch.object(Submission, "query", create=True)
    mock_model.filter_by.return_value.order_by.return_value.first.return_value = None

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
    with client.session_transaction() as sess:
        sess["user_id"] = "stu1"
    response = client.post("/rerun_submission_autograder", json={})

    assert response.status_code == 400
    assert response.get_json()["message"] == "Missing submission_id"


def test_rerun_submission_autograder_requires_configured_autograder(client, mocker):
    with client.session_transaction() as sess:
        sess["user_id"] = "stu1"

    existing_submission = mocker.Mock()
    existing_submission.id = "sub1"
    existing_submission.assignment_id = "assgn1"

    assignment = mocker.Mock()
    assignment.id = "assgn1"
    assignment.autograder_image_name = ""

    def fake_get(model, item_id):
        if model.__name__ == "Submission":
            return existing_submission
        if model.__name__ == "Assignment":
            return assignment
        return None

    mocker.patch("routes.submission.db.session.get", side_effect=fake_get)

    response = client.post(
        "/rerun_submission_autograder",
        json={"submission_id": "sub1"},
    )

    assert response.status_code == 400
    assert "No autograder configured" in response.get_json()["message"]


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
    data = response.get_json()
    assert data["message"] == "No active submission found"
    assert data["data"] is None


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
    response = client.delete("/delete_submission?submission_id=123")
    assert response.status_code == 404
    data = response.get_json()
    assert data["message"] == "No submission found to delete"


# FAILED TEST
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
    fake_submission = mocker.Mock()
    fake_submission.assignment_id = "assgn1"

    # Patch the get method on the api.db.session instead of routes.submission.db.session.get
    fake_get = mocker.patch("api.db.session.get", return_value=fake_submission)
    mock_delete = mocker.patch("routes.submission.db.session.delete")
    mock_commit = mocker.patch("routes.submission.db.session.commit")

    response = client.delete("/delete_submission?submission_id=123")
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Submission successfully deleted"
    
    fake_get.assert_called_once_with(Submission, "123")
    mock_delete.assert_called_once_with(fake_submission)
    mock_commit.assert_called_once()

def test_get_active_submission_missing_params(client):
    response = client.get("/get_active_submission")
    assert response.status_code == 400

    data = response.get_json(silent=True)
    assert data is not None, "Expected a valid JSON response"
    assert data["message"] == "not sufficient details"


# Tests for /export_evaluations


def test_export_evaluations_missing_assignment_id(client):
    response = client.get("/export_evaluations")
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Missing assignment_id"


def test_export_evaluations_assignment_not_found(client, mocker):
    mocker.patch("routes.submission.db.session.query").return_value.filter_by.return_value.first.return_value = None
    response = client.get("/export_evaluations?assignment_id=missing-assignment")
    assert response.status_code == 404
    data = response.get_json()
    assert data["message"] == "Assignment not found"


def test_export_evaluations_no_graded_results(app, client):
    with app.app_context():
        assignment_id = str(uuid.uuid4())
        db.session.add(Assignment(id=assignment_id, name="No Results Yet", course_id=str(uuid.uuid4())))
        db.session.commit()

    response = client.get(f"/export_evaluations?assignment_id={assignment_id}")
    assert response.status_code == 200

    zf = zipfile.ZipFile(io.BytesIO(response.data))
    assert zf.namelist() == ["README.txt"]
    assert "No graded test results found" in zf.read("README.txt").decode()


def _make_student(name, email, sis_id):
    return User(
        id=str(uuid.uuid4()),
        password="pw",
        name=name,
        email_address=email,
        sis_user_id=sis_id,
        role="student",
    )


def test_export_evaluations_success(app, client):
    with app.app_context():
        assignment_id = str(uuid.uuid4())
        course_id = str(uuid.uuid4())
        instructor_id = str(uuid.uuid4())
        base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

        alice = _make_student("Alice Example", "alice@example.com", "alice")
        bob = _make_student("Bob Example", "bob@example.com", "bob")
        carol = _make_student("Carol Example", "carol@example.com", "carol")
        # Dave is enrolled but never submits, to verify non-submitters still
        # show up in the export instead of silently disappearing.
        dave = _make_student("Dave Example", "dave@example.com", "dave")

        db.session.add(Course(
            id=course_id,
            name="CS 101",
            instructor_id=instructor_id,
            semester="Fall",
            year="2026",
            entryCode=f"entry-{course_id[:8]}",
        ))
        db.session.add(Assignment(id=assignment_id, name="HW1", course_id=course_id))
        db.session.add_all([alice, bob, carol, dave])
        db.session.add_all([
            Enrollment(student_id=alice.id, course_id=course_id, role="student"),
            Enrollment(student_id=bob.id, course_id=course_id, role="student"),
            Enrollment(student_id=carol.id, course_id=course_id, role="student"),
            Enrollment(student_id=dave.id, course_id=course_id, role="student"),
        ])

        alice_results = json.dumps({
            "tests": [
                {"name": "Evaluate 8 / 4 * 2", "number": "2.3", "status": "passed",
                 "score": 1, "max_score": 1, "output": "42", "expected_output": "42"},
                {"name": "Check submitted files", "status": "failed", "score": 0,
                 "max_score": 1, "output": "wrong", "expected_output": "hello"},
            ],
            "score": 1,
        }).encode()
        bob_results = json.dumps({
            "tests": [
                {"name": "Evaluate 8 / 4 * 2", "number": "2.3", "status": "passed",
                 "score": 1, "max_score": 1, "output": "42", "expected_output": "42"},
            ],
            "score": 1,
        }).encode()

        db.session.add(Submission(
            id=str(uuid.uuid4()),
            file_name="alice.py",
            submission_number=1,
            student_id=alice.id,
            assignment_id=assignment_id,
            student_code_file=b"print(42)",
            results=alice_results,
            active=True,
            completed=True,
            submitted_at=base_time,
        ))
        db.session.add(Submission(
            id=str(uuid.uuid4()),
            file_name="bob.py",
            submission_number=1,
            student_id=bob.id,
            assignment_id=assignment_id,
            student_code_file=b"print(42)",
            results=bob_results,
            active=True,
            completed=True,
            submitted_at=base_time + timedelta(minutes=1),
        ))
        db.session.add(Submission(
            id=str(uuid.uuid4()),
            file_name="carol.py",
            submission_number=1,
            student_id=carol.id,
            assignment_id=assignment_id,
            student_code_file=b"print(0)",
            results=b"not valid json",
            active=True,
            completed=True,
            submitted_at=base_time + timedelta(minutes=2),
        ))
        db.session.commit()

    response = client.get(f"/export_evaluations?assignment_id={assignment_id}")
    assert response.status_code == 200
    assert "HW1_evaluations.zip" in response.headers.get("Content-Disposition", "")

    zf = zipfile.ZipFile(io.BytesIO(response.data))
    # Numbered test -> filename keyed off "number", not the mangled name.
    # Unnumbered test -> falls back to the sanitized name.
    assert set(zf.namelist()) == {"Question_2.3.csv", "Check_submitted_files.csv"}

    q1_rows = list(csv.DictReader(io.StringIO(zf.read("Question_2.3.csv").decode())))
    assert q1_rows == [
        {
            "question": "Evaluate 8 / 4 * 2",
            "student_name": "Alice Example",
            "student_email": "alice@example.com",
            "status": "passed",
            "score": "1",
            "max_score": "1",
            "output": "42",
            "expected_output": "42",
        },
        {
            "question": "Evaluate 8 / 4 * 2",
            "student_name": "Bob Example",
            "student_email": "bob@example.com",
            "status": "passed",
            "score": "1",
            "max_score": "1",
            "output": "42",
            "expected_output": "42",
        },
        {
            "question": "Evaluate 8 / 4 * 2",
            "student_name": "Carol Example",
            "student_email": "carol@example.com",
            "status": "",
            "score": "",
            "max_score": "",
            "output": "",
            "expected_output": "",
        },
        {
            "question": "Evaluate 8 / 4 * 2",
            "student_name": "Dave Example",
            "student_email": "dave@example.com",
            "status": "no submission",
            "score": "",
            "max_score": "",
            "output": "",
            "expected_output": "",
        },
    ]

    q2_rows = list(csv.DictReader(io.StringIO(zf.read("Check_submitted_files.csv").decode())))
    assert q2_rows == [
        {
            "question": "Check submitted files",
            "student_name": "Alice Example",
            "student_email": "alice@example.com",
            "status": "failed",
            "score": "0",
            "max_score": "1",
            "output": "wrong",
            "expected_output": "hello",
        },
        {
            "question": "Check submitted files",
            "student_name": "Bob Example",
            "student_email": "bob@example.com",
            "status": "",
            "score": "",
            "max_score": "",
            "output": "",
            "expected_output": "",
        },
        {
            "question": "Check submitted files",
            "student_name": "Carol Example",
            "student_email": "carol@example.com",
            "status": "",
            "score": "",
            "max_score": "",
            "output": "",
            "expected_output": "",
        },
        {
            "question": "Check submitted files",
            "student_name": "Dave Example",
            "student_email": "dave@example.com",
            "status": "no submission",
            "score": "",
            "max_score": "",
            "output": "",
            "expected_output": "",
        },
    ]

