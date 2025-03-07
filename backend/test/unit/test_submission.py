# test_submission.py

import pytest
from flask import Flask
from api import create_app

# Assuming your submission blueprint is registered in create_app
# If not, you'll need to import the blueprint and register it manually.

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Use your test config class or similar setup
    app = create_app(config_class="config.TestConfig")
    
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def mock_submission_query(mocker):
    """
    Example fixture that patches out db.session.query and SubmissionSchema 
    from your submission route module.
    """
    # Adjust the import path to where your submission blueprint code resides.
    # For example, if you have from routes.submission import submission,
    # you might patch "routes.submission.db.session.query"
    mock_query = mocker.patch("submission.db.session.query")
    mock_schema = mocker.patch("submission.SubmissionSchema")
    return mock_query, mock_schema


def test_get_submissions_success(client, mock_submission_query, mocker):
    """
    Test a successful GET request to /get_submissions
    """
    mock_query, mock_schema = mock_submission_query

    # Mock the DB query result
    # e.g., .all() returns a list of Submission objects (or Mocks)
    mock_submission_obj = mocker.Mock()
    mock_query.return_value.filter_by.return_value.all.return_value = [mock_submission_obj]

    # Mock the schema dump
    mock_schema.return_value.dump.return_value = [
        {
            "id": "fake-submission-id",
            "student_id": "fake-student-id",
            "assignment_id": "fake-assignment-id",
        }
    ]

    # Make the request with valid query parameters
    response = client.get("/get_submissions?student_id=123&assignment_id=456")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "fake-submission-id"

    # Ensure the DB query was called once with the correct filters
    mock_query.assert_called_once()
    mock_query.return_value.filter_by.assert_called_once_with(student_id="123", assignment_id="456")
    # And that we called .all() on that query
    mock_query.return_value.filter_by.return_value.all.assert_called_once()


def test_get_submissions_not_found(client, mock_submission_query, mocker):
    """
    Test the case where /get_submissions returns no submissions
    """
    mock_query, mock_schema = mock_submission_query

    # Mock the DB query to return an empty list
    mock_query.return_value.filter_by.return_value.all.return_value = []

    response = client.get("/get_submissions?student_id=999&assignment_id=999")

    assert response.status_code == 404
    assert response.get_json()["message"] == "No submissions found for the provided student and assignment"


def test_get_submissions_missing_params(client):
    """
    Test /get_submissions with missing parameters
    """
    # No student_id or assignment_id provided
    response = client.get("/get_submissions")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Missing student_id or assignment_id"


def test_upload_submission_success(client, mocker):
    """
    Test a successful file upload to /upload_submission
    Here we patch out Docker and DB commits to avoid real external calls.
    """
    # Patch out Docker calls and DB
    mock_db_add = mocker.patch("submission.db.session.add")
    mock_db_commit = mocker.patch("submission.db.session.commit")
    mock_assignment_query = mocker.patch("submission.db.session.query")
    mock_subprocess_run = mocker.patch("submission.subprocess.run")
    mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data=b'fake-binary-data'))

    # Mock the assignment object to return from the DB
    mock_assignment_obj = mocker.Mock()
    mock_assignment_obj.container_id = "fake-container-id"
    mock_assignment_obj.autograder_timeout = 10

    mock_assignment_query.return_value.filter_by.return_value.first.return_value = mock_assignment_obj

    # For the Docker calls, we can simulate success by setting returncode = 0
    mock_completed_process = mocker.Mock()
    mock_completed_process.returncode = 0
    mock_completed_process.stdout = b'{"score": 100, "execution_time": 1.23}'
    mock_subprocess_run.return_value = mock_completed_process

    # Build the form data, including the file
    data = {
        "assignment_id": "fake-assignment-id",
        "student_id": "fake-student-id"
    }
    # We'll send a small dummy file
    file_data = {
        "file": (b"print('hello world')", "test.py"),
    }

    response = client.post(
        "/upload_submission",
        content_type='multipart/form-data',
        data={**data, **file_data}
    )

    assert response.status_code == 200
    result = response.get_json()
    assert result["message"] == "Submission uploaded and autograded successfully"
    assert "submissionID" in result

    # Check that DB was updated
    mock_db_add.assert_called_once()
    mock_db_commit.assert_called_once()


def test_upload_submission_no_file(client):
    """
    Test /upload_submission without providing a file.
    It should raise a BadRequestError or return 400.
    """
    response = client.post(
        "/upload_submission",
        data={"assignment_id": "fake-assign", "student_id": "fake-student"},
        content_type='multipart/form-data'
    )
    assert response.status_code == 400  # or 500 if you raise an exception
    assert b"No file part" in response.data


# You can keep adding more tests for other endpoints, e.g., /delete_submission,
# /get_active_submission, /activate_submission, etc., following similar patterns.
