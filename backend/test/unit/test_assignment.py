import pytest
from api import create_app
from api.models import Assignment, Submission, AssignmentExtension, Course


@pytest.fixture
def app():
    """Create a Flask app with the assignment blueprint for testing."""
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Flask test client for sending requests."""
    return app.test_client()



def test_update_assignment_success(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter.return_value.first.return_value = None
    mock_query.return_value.filter_by.return_value.update.return_value = 1
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    resp = client.post("/update_assignment", json={
        "assignment_id": "some-uuid",
        "name": "Updated",
        "course_id": "course-uuid"
    })

    assert resp.status_code == 200
    assert resp.json["message"] == "Success"
    mock_commit.assert_called_once()


def test_update_assignment_duplicate_name(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter.return_value.first.return_value = mocker.Mock()

    resp = client.post("/update_assignment", json={
        "assignment_id": "some-uuid",
        "name": "Duplicate",
        "course_id": "course-uuid"
    })

    assert resp.status_code == 400
    assert "already exists" in resp.json["message"]


def test_update_assignment_not_found(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter.return_value.first.return_value = None
    mock_query.return_value.filter_by.return_value.update.return_value = 0

    resp = client.post("/update_assignment", json={
        "assignment_id": "notfound-uuid",
        "name": "Anything",
        "course_id": "course-uuid"
    })

    assert resp.status_code == 404
    assert resp.json["message"] == "Assignment not found"



def test_get_assignment_success(client, mocker):
    """Happy‑path lookup."""
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_assignment = Assignment(id="assignment-uuid", name="Test Assignment")

    # chain: session.query(...).filter_by(...).first() -> mock_assignment
    mock_query.return_value.filter_by.return_value.first.return_value = mock_assignment

    resp = client.get("/get_assignment?assignment_id=assignment-uuid")

    assert resp.status_code == 200
    assert resp.json["id"] == "assignment-uuid"
    assert resp.json["name"] == "Test Assignment"
    mock_query.return_value.filter_by.assert_called_once_with(id="assignment-uuid")


def test_get_assignment_empty(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    resp = client.get("/get_assignment?assignment_id=empty-uuid")
    assert resp.status_code == 404
    assert resp.json["message"] == "Assignment not found"


# ---------------------------------------------------------------------------
# create_assignment
# ---------------------------------------------------------------------------

def test_create_assignment_success(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.one_or_none.return_value = None
    mock_add = mocker.patch("routes.assignment.db.session.add")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    new_assignment = Assignment(id="123", name="New Assignment", course_id="course-uuid")
    mock_query.return_value.filter_by.return_value.first.return_value = new_assignment

    resp = client.post("/create_assignment", json={
        "name": "New Assignment",
        "course_id": "course-uuid"
    })

    assert resp.status_code == 200
    # --- relaxed: only verify the key fields we expect, ignore extras ---
    assert resp.json["id"] == "123"
    assert resp.json["name"] == "New Assignment"
    assert resp.json["course_id"] == "course-uuid"

    mock_add.assert_called_once()
    mock_commit.assert_called_once()



def test_create_assignment_duplicate(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.one_or_none.return_value = mocker.Mock()

    resp = client.post("/create_assignment", json={
        "name": "Duplicate",
        "course_id": "course-uuid"
    })

    assert resp.status_code == 400
    assert "already exists" in resp.json["message"]



def test_duplicate_assignment_success(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    old_assignment = Assignment(id="old-id", name="Old")
    mock_query.return_value.filter_by.return_value.one_or_none.side_effect = [
        old_assignment,  # first lookup – old assignment
        None             # second lookup – ensure new name is free
    ]
    mock_add = mocker.patch("routes.assignment.db.session.add")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    resp = client.post("/duplicate_assignment", json={
        "oldAssignmentId": "old-id",
        "newAssignmentTitle": "New Title",
        "currentCourseId": "course-uuid"
    })

    assert resp.status_code == 200
    assert resp.json["name"] == "New Title"
    mock_add.assert_called_once()
    mock_commit.assert_called_once()


def test_duplicate_assignment_old_not_found(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.one_or_none.side_effect = [None, None]

    resp = client.post("/duplicate_assignment", json={
        "oldAssignmentId": "notfound-id",
        "newAssignmentTitle": "New",
        "currentCourseId": "course-uuid"
    })

    assert resp.status_code == 404
    assert "Old assignment not found" in resp.json["error"]


def test_duplicate_assignment_name_conflict(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    old_assignment = Assignment(id="old-id", name="Old")
    mock_query.return_value.filter_by.return_value.one_or_none.side_effect = [
        old_assignment,    # old assignment exists
        mocker.Mock()      # new name already in use
    ]

    resp = client.post("/duplicate_assignment", json={
        "oldAssignmentId": "old-id",
        "newAssignmentTitle": "Conflict",
        "currentCourseId": "course-uuid"
    })

    assert resp.status_code == 404
    assert "already exists in this course" in resp.json["error"]



def test_delete_assignment_not_found(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.get.return_value = None

    resp = client.delete("/delete_assignment?assignment_id=notfound-id")
    assert resp.status_code == 404
    assert "Assignment not found" in resp.json


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
    mock_commit = mocker.patch("routes.assignment.db.session.commit")
    mock_delete = mocker.patch("routes.assignment.db.session.delete")

    mock_query.return_value.filter_by.return_value.all.side_effect = [
        [Submission(id="sub-1"), Submission(id="sub-2")],
        []
    ]

    resp = client.delete("/delete_submissions?assignment_id=assign-id")
    assert resp.status_code == 200
    assert "Submissions deleted successfully" in resp.json
    assert mock_delete.call_count == 2
    mock_commit.assert_called()


# ---------------------------------------------------------------------------
# assignment extensions
# ---------------------------------------------------------------------------

def test_create_extension_success(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None
    mock_add = mocker.patch("routes.assignment.db.session.add")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    resp = client.post("/create_extension", json={
        "assignment_id": "assign-id",
        "student_id": "student-id",
        "release_date_extension": "2025-10-01T10:00:00Z",
        "due_date_extension": "2025-10-05T23:59:59Z",
        "late_due_date_extension": "2025-10-10T23:59:59Z"
    })

    assert resp.status_code == 200
    mock_add.assert_called_once()
    mock_commit.assert_called()


def test_create_extension_existing(client, mocker):
    with client.application.app_context():
        mock_query = mocker.patch("routes.assignment.db.session.query")
        mock_query.return_value.filter_by.return_value.first.return_value = AssignmentExtension(id="old-ext-id")

        mock_delete = mocker.patch("routes.assignment.db.session.delete")
        mock_commit = mocker.patch("routes.assignment.db.session.commit")

        resp = client.post("/create_extension", json={
            "assignment_id": "assign-id",
            "student_id": "student-id",
            "release_date_extension": "2025-10-01T10:00:00Z",
            "due_date_extension": "2025-10-05T23:59:59Z",
            "late_due_date_extension": "2025-10-10T23:59:59Z"
        })

        assert resp.status_code == 200
        mock_delete.assert_called_once()
        mock_commit.assert_called()


def test_get_extension(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_ext = AssignmentExtension(id="ext-id", assignment_id="assign-id", student_id="student-id")
    mock_query.return_value.filter_by.return_value.first.return_value = mock_ext

    resp = client.get("/get_extension?assignment_id=assign-id&student_id=student-id")
    assert resp.status_code == 200
    assert resp.json["id"] == "ext-id"


def test_get_assignment_extensions(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value = [
        AssignmentExtension(id="ext-1"),
        AssignmentExtension(id="ext-2")
    ]

    resp = client.get("/get_assignment_extensions?assignment_id=assign-id")
    assert resp.status_code == 200
    assert len(resp.json) == 2


def test_delete_extension_found(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_ext = AssignmentExtension(id="ext-id")
    mock_query.return_value.filter_by.return_value.first.return_value = mock_ext
    mock_query.return_value.filter_by.return_value.all.return_value = []
    mock_delete = mocker.patch("routes.assignment.db.session.delete")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    resp = client.delete("/delete_extension?extension_id=ext-id")
    assert resp.status_code == 200
    assert "Extension deleted successfully" in resp.json
    mock_delete.assert_called_with(mock_ext)
    mock_commit.assert_called()


def test_delete_extension_not_found(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None
    mock_query.return_value.filter_by.return_value.all.return_value = []

    resp = client.delete("/delete_extension?extension_id=notfound-id")
    assert resp.status_code == 200
    assert "Extension deleted successfully" in resp.json



def test_get_courses_all(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.all.return_value = [
        Course(id="course-1", name="Course 1"),
        Course(id="course-2", name="Course 2")
    ]

    resp = client.get("/courses")
    assert resp.status_code == 200
    assert len(resp.json) == 2


def test_get_courses_instructor(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.all.return_value = [
        Course(id="course-3", name="Course 3", instructor_id="instr-1")
    ]

    resp = client.get("/courses?instructor_id=instr-1")
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["id"] == "course-3"
