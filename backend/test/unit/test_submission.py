import os
import pytest
from flask import json
from api import create_app, db
from api.models import Submission


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
    assert data["error"] == "Missing student_id or assignment_id"


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
    assert data["error"] == "Missing student_id or assignment_id"


def test_get_latest_submission_success(client, mocker):
    """Test /get_latest_submission returns the latest submission data."""
    fake_submission = {"id": "sub1", "score": 100}
    # Patch the query chain for Submission.
    fake_query = mocker.patch("routes.submission.Submission.query")
    fake_query.filter_by.return_value.order_by.return_value.first.return_value = fake_submission

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submission

    response = client.get("/get_latest_submission?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == fake_submission


def test_get_latest_submission_not_found(client, mocker):
    """Test /get_latest_submission returns a message when no submission is found."""
    fake_query = mocker.patch("routes.submission.Submission.query")
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
    assert data["error"] == "Missing submission_id"


# Tests for activating a submission


def test_activate_submission_missing_params(client):
    """Test /activate_submission returns error if required fields are missing."""
    payload = {"submission_id": "sub1", "student_id": "stu1"}  # missing assignment_id
    response = client.post("/activate_submission", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Missing submission_id, student_id or assignment_id"


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
    assert data["error"] == "Missing submission id"


def test_get_submission_details_success(client, mocker):
    """Test /get_submission_details returns submission details when found."""
    fake_submission = {"id": "sub1", "score": 100}
    dummy_query = mocker.patch("routes.submission.db.session.query")
    # Simulate the query returning an object that will be dumped as a list with one item.
    dummy_query.return_value.filter_by.return_value = fake_submission

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = [fake_submission]

    response = client.get("/get_submission_details?submission_id=sub1")
    assert response.status_code == 200
    assert response.get_json() == fake_submission


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
    assert response.get_json() == {"message": "no such submission found"}


# Edge cases to add in route implementations


def test_upload_submission_missing_file(client):
    """Test /upload_submission returns error when file is missing."""
    # Note: Depending on your app error handling, this might raise an exception.
    response = client.post("/upload_submission", data={})
    # We expect a 400 error for missing file
    assert response.status_code == 400


# FAILED TEST
def test_delete_submission_not_found(client, mocker):
    """Test /delete_submission returns 404 when the submission is not found."""
    # Patch the get method to return None.
    mocker.patch("routes.submission.Submission.query.get", return_value=None)
    
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
    fake_submission = object()  # a dummy submission object

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
    
    error_message = data.get("error") or data.get("message")
    assert error_message is not None, "Expected JSON response to contain 'error' or 'message' key"
    assert error_message == "not sufficient details"