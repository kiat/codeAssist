import pytest
from flask import Flask
from routes.assignment import assignment
from api.models import Assignment, Submission

@pytest.fixture
def app():
    """Create a Flask app with the assignment blueprint for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(assignment, url_prefix="/")
    return app

@pytest.fixture
def client(app):
    """Flask test client for sending requests."""
    return app.test_client()

#Test cases

def test_update_assignment_success(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter.return_value.first.return_value = None
    mock_query.return_value.filter_by.return_value.update.return_value = 1
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    data = {
        "assignment_id": "some-uuid",
        "name": "Updated",
        "course_id": "course-uuid"
    }
    resp = client.post("/update_assignment", json=data)
    assert resp.status_code == 200
    assert resp.json["message"] == "Success"
    mock_commit.assert_called_once()


def test_update_assignment_duplicate_name(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter.return_value.first.return_value = mocker.Mock()

    data = {
        "assignment_id": "some-uuid",
        "name": "DuplicateName",
        "course_id": "course-uuid"
    }
    resp = client.post("/update_assignment", json=data)
    assert resp.status_code == 400
    assert "already exists" in resp.json["message"]


def test_update_assignment_not_found(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter.return_value.first.return_value = None
    mock_query.return_value.filter_by.return_value.update.return_value = 0

    data = {
        "assignment_id": "notfound-uuid",
        "name": "Anything",
        "course_id": "course-uuid"
    }
    resp = client.post("/update_assignment", json=data)
    assert resp.status_code == 404
    assert resp.json["message"] == "Assignment not found"


def test_get_assignment_success(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_assignment = Assignment(id="assignment-uuid", name="Test Assignment")
    mock_query.return_value.filter_by.return_value = mock_assignment

    resp = client.get("/get_assignment?assignment_id=assignment-uuid")
    assert resp.status_code == 200
    assert resp.json["id"] == "assignment-uuid"
    assert resp.json["name"] == "Test Assignment"


def test_create_assignment_success(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.one_or_none.return_value = None
    mock_add = mocker.patch("routes.assignment.db.session.add")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    new_assignment = Assignment(id=123, name="New Assignment", course_id="course-uuid")
    mock_query.return_value.filter_by.return_value.first.return_value = new_assignment

    data = {"name": "New Assignment", "course_id": "course-uuid"}
    resp = client.post("/create_assignment", json=data)

    assert resp.status_code == 200
    assert resp.json["id"] == "123"
    assert resp.json["name"] == "New Assignment"
    assert resp.json["course_id"] == "course-uuid"

    mock_add.assert_called_once()
    mock_commit.assert_called_once()


def test_duplicate_assignment_success(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    old_assignment = Assignment(id="old-id", name="Old Assignment")
    mock_query.return_value.filter_by.return_value.one_or_none.side_effect = [old_assignment, None]
    mock_add = mocker.patch("routes.assignment.db.session.add")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    data = {
        "oldAssignmentId": "old-id",
        "newAssignmentTitle": "New Title",
        "currentCourseId": "course-uuid"
    }
    resp = client.post("/duplicate_assignment", json=data)
    assert resp.status_code == 200
    assert resp.json["name"] == "New Title"
    mock_add.assert_called_once()
    mock_commit.assert_called_once()


def test_delete_assignment_with_submissions(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_submission = Submission(id="sub-id", assignment_id="assign-id")
    mock_query.return_value.filter_by.return_value.all.return_value = [mock_submission]
    mock_query.return_value.get.return_value = Assignment(id="assign-id")

    mock_delete = mocker.patch("routes.assignment.db.session.delete")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    resp = client.delete("/delete_assignment?assignment_id=assign-id")
    assert resp.status_code == 200
    assert "Assignment deleted successfully" in resp.json
    assert mock_delete.call_count >= 2
    mock_commit.assert_called()


def test_delete_submissions(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_delete = mocker.patch("routes.assignment.db.session.delete")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    mock_query.return_value.filter_by.return_value.all.side_effect = [
        [Submission(id="sub-1"), Submission(id="sub-2")],
        []
    ]
    resp = client.delete("/delete_submissions?assignment_id=assign-id")
    assert resp.status_code == 200
    assert "Submissions deleted successfully" in resp.json
    assert mock_delete.call_count == 2
    mock_commit.assert_called()


def test_create_extension_success(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None
    mock_add = mocker.patch("routes.assignment.db.session.add")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    data = {
        "assignment_id": "assign-id",
        "student_id": "student-id",
        "release_date_extension": "2025-10-01T10:00:00Z",
        "due_date_extension": "2025-10-05T23:59:59Z",
        "late_due_date_extension": "2025-10-10T23:59:59Z"
    }
    resp = client.post("/create_extension", json=data)
    assert resp.status_code == 200
    mock_add.assert_called_once()
    mock_commit.assert_called()
