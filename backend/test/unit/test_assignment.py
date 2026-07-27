import pytest
from api import create_app
from api.models import Assignment, Submission, AssignmentExtension, Course, Enrollment


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


def _mock_course_role(mocker, role="instructor"):
    return mocker.patch("util.auth.get_user_course_role", return_value=role)


def mock_ai_feedback_route_queries(mocker, assignment):
    course = Course(id=assignment.course_id, instructor_id="instructor-uuid")

    assignment_query = mocker.Mock()
    assignment_query.filter_by.return_value.first.return_value = assignment

    course_query = mocker.Mock()
    course_query.filter_by.return_value.first.return_value = course

    enrollment_query = mocker.Mock()
    enrollment_query.filter_by.return_value.first.return_value = None

    def query_side_effect(model):
        if model is Assignment:
            return assignment_query
        if model is Course:
            return course_query
        if model is Enrollment:
            return enrollment_query
        raise AssertionError(f"Unexpected model queried: {model}")

    mock_query = mocker.patch("routes.ai_feedback.db.session.query")
    mock_query.side_effect = query_side_effect
    return mock_query



def test_update_assignment_success(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter.return_value.first.return_value = None
    mock_query.return_value.filter_by.return_value.update.return_value = 1
    mock_commit = mocker.patch("routes.assignment.db.session.commit")
    _mock_course_role(mocker)
    login_as("instructor-uuid")

    resp = client.put("/update_assignment", json={
        "assignment_id": "some-uuid",
        "name": "Updated",
        "course_id": "course-uuid"
    })

    assert resp.status_code == 200
    assert resp.json["message"] == "Assignment updated successfully"
    mock_commit.assert_called_once()


def test_update_assignment_duplicate_name(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter.return_value.first.return_value = mocker.Mock()
    _mock_course_role(mocker)
    login_as("instructor-uuid")

    resp = client.put("/update_assignment", json={
        "assignment_id": "some-uuid",
        "name": "Duplicate",
        "course_id": "course-uuid"
    })

    assert resp.status_code == 400
    assert "already exists" in resp.json["message"]


def test_update_assignment_not_found(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter.return_value.first.return_value = None
    mock_query.return_value.filter_by.return_value.first.return_value = None
    _mock_course_role(mocker)
    login_as("instructor-uuid")

    resp = client.put("/update_assignment", json={
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


def test_get_assignment_does_not_return_assignment_api_key(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_assignment = Assignment(
        id="assignment-uuid",
        name="AI Assignment",
        course_id="course-uuid",
        ai_feedback_api_key="encrypted-assignment-key",
    )

    mock_query.return_value.filter_by.return_value.first.return_value = mock_assignment

    resp = client.get("/get_assignment?assignment_id=assignment-uuid")

    assert resp.status_code == 200
    assert resp.json["has_assignment_ai_key"] is True
    assert "ai_feedback_api_key" not in resp.json


def test_get_assignment_empty(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    resp = client.get("/get_assignment?assignment_id=empty-uuid")
    assert resp.status_code == 404
    assert resp.json["message"] == "Assignment not found"


def test_get_assignment_ai_settings_returns_normalized_defaults(client, mocker):
    mock_assignment = Assignment(
        id="assignment-uuid",
        name="AI Assignment",
        course_id="course-uuid",
        ai_feedback_enabled=True,
        use_course_ai_default=True,
    )
    mock_ai_feedback_route_queries(mocker, mock_assignment)

    with client.session_transaction() as sess:
        sess["user_id"] = "instructor-uuid"

    resp = client.get("/assignments/assignment-uuid/ai-settings")

    assert resp.status_code == 200
    assert resp.json["ai_feedback_enabled"] is True
    assert resp.json["ai_feedback_prompts"][0]["id"] == "check_correctness"
    assert resp.json["ai_allowed_inputs"]["student_code"] is True
    assert resp.json["ai_allowed_inputs"]["test_cases"] is False
    assert "feedback_prompts" not in resp.json
    assert "allowed_inputs" not in resp.json
    assert resp.json["ai_feedback_max_requests"] is None
    assert resp.json["ai_feedback_wait_seconds"] == 0


def test_update_assignment_ai_settings_saves_prompts_and_allowed_inputs(client, mocker):
    mock_assignment = Assignment(
        id="assignment-uuid",
        name="AI Assignment",
        course_id="course-uuid",
        ai_feedback_enabled=True,
    )
    mock_ai_feedback_route_queries(mocker, mock_assignment)
    mock_commit = mocker.patch("routes.ai_feedback.db.session.commit")

    with client.session_transaction() as sess:
        sess["user_id"] = "instructor-uuid"

    resp = client.put(
        "/assignments/assignment-uuid/ai-settings",
        json={
            "feedback_prompts": [
                {
                    "id": "debug_failed_tests",
                    "title": "Debug Failed Tests",
                    "prompt": "Explain failed tests without solving.",
                    "enabled": True,
                }
            ],
            "allowed_inputs": {
                "assignment_description": True,
                "student_code": False,
                "test_results": True,
                "test_cases": False,
                "student_output": False,
            },
            "ai_feedback_max_requests": 3,
            "ai_feedback_wait_seconds": 60,
        },
    )

    assert resp.status_code == 200
    assert mock_assignment.ai_feedback_prompts[0]["id"] == "debug_failed_tests"
    assert mock_assignment.ai_feedback_prompt == "Explain failed tests without solving."
    assert mock_assignment.ai_allowed_inputs["student_code"] is False
    assert mock_assignment.ai_allowed_inputs["student_output"] is False
    assert mock_assignment.ai_feedback_max_requests == 3
    assert mock_assignment.ai_feedback_wait_seconds == 60
    mock_commit.assert_called_once()


def test_update_assignment_ai_settings_rejects_invalid_prompt(client, mocker):
    mock_assignment = Assignment(
        id="assignment-uuid",
        name="AI Assignment",
        course_id="course-uuid",
    )
    mock_ai_feedback_route_queries(mocker, mock_assignment)
    mock_rollback = mocker.patch("routes.ai_feedback.db.session.rollback")

    with client.session_transaction() as sess:
        sess["user_id"] = "instructor-uuid"

    resp = client.put(
        "/assignments/assignment-uuid/ai-settings",
        json={
            "feedback_prompts": [
                {
                    "id": "invalid",
                    "title": "",
                    "prompt": "Explain failed tests.",
                    "enabled": True,
                }
            ]
        },
    )

    assert resp.status_code == 400
    assert "Prompt title is required" in resp.json["message"]
    mock_rollback.assert_called_once()


# ---------------------------------------------------------------------------
# create_assignment
# ---------------------------------------------------------------------------

def test_create_assignment_success(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.one_or_none.return_value = None
    mock_add = mocker.patch("routes.assignment.db.session.add")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    new_assignment = Assignment(id="123", name="New Assignment", course_id="course-uuid")
    mock_query.return_value.filter_by.return_value.first.return_value = new_assignment
    _mock_course_role(mocker)
    login_as("instructor-uuid")

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



def test_create_assignment_duplicate(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.one_or_none.return_value = mocker.Mock()
    _mock_course_role(mocker)
    login_as("instructor-uuid")

    resp = client.post("/create_assignment", json={
        "name": "Duplicate",
        "course_id": "course-uuid"
    })

    assert resp.status_code == 400
    assert "already exists" in resp.json["message"]



def test_duplicate_assignment_success(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    old_assignment = Assignment(id="old-id", name="Old")
    mock_query.return_value.filter_by.return_value.one_or_none.side_effect = [
        old_assignment,  # first lookup – old assignment
        None             # second lookup – ensure new name is free
    ]
    mock_add = mocker.patch("routes.assignment.db.session.add")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")
    _mock_course_role(mocker)
    login_as("instructor-uuid")

    resp = client.post("/duplicate_assignment", json={
        "oldAssignmentId": "old-id",
        "newAssignmentTitle": "New Title",
        "currentCourseId": "course-uuid"
    })

    assert resp.status_code == 200
    assert resp.json["name"] == "New Title"
    mock_add.assert_called_once()
    mock_commit.assert_called_once()


def test_duplicate_assignment_old_not_found(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.one_or_none.side_effect = [None, None]
    _mock_course_role(mocker)
    login_as("instructor-uuid")

    resp = client.post("/duplicate_assignment", json={
        "oldAssignmentId": "notfound-id",
        "newAssignmentTitle": "New",
        "currentCourseId": "course-uuid"
    })

    assert resp.status_code == 404
    assert "Old assignment not found" in resp.json["message"]


def test_duplicate_assignment_name_conflict(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    old_assignment = Assignment(id="old-id", name="Old")
    mock_query.return_value.filter_by.return_value.one_or_none.side_effect = [
        old_assignment,    # old assignment exists
        mocker.Mock()      # new name already in use
    ]
    _mock_course_role(mocker)
    login_as("instructor-uuid")

    resp = client.post("/duplicate_assignment", json={
        "oldAssignmentId": "old-id",
        "newAssignmentTitle": "Conflict",
        "currentCourseId": "course-uuid"
    })

    assert resp.status_code == 404
    assert "already exists in this course" in resp.json["message"]



def test_delete_assignment_not_found(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    with client.session_transaction() as sess:
        sess["user_id"] = "instructor-uuid"

    resp = client.delete("/delete_assignment?assignment_id=notfound-id")
    assert resp.status_code == 404
    assert "Assignment not found" in resp.json["message"]


def test_delete_assignment_with_submissions(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_delete = mocker.patch("routes.assignment.db.session.delete")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")

    mock_assignment = Assignment(id="assign-id", course_id="course-uuid")
    mock_enrollment = mocker.Mock()
    mock_enrollment.role = "instructor"
    mock_submission = Submission(id="sub-id", assignment_id="assign-id")

    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_assignment,   # assignment auth lookup
        mock_enrollment,   # enrollment auth lookup
    ]
    mock_query.return_value.filter.return_value.all.return_value = [mock_submission]
    mock_query.return_value.filter_by.return_value.delete.return_value = None

    with client.session_transaction() as sess:
        sess["user_id"] = "instructor-uuid"

    resp = client.delete("/delete_assignment?assignment_id=assign-id")
    assert resp.status_code == 200
    assert "Assignment deleted successfully" in resp.json["message"]
    assert mock_delete.call_count >= 1
    mock_commit.assert_called()


def test_delete_submissions(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")
    mock_delete = mocker.patch("routes.assignment.db.session.delete")

    mock_assignment = Assignment(id="assign-id", course_id="course-uuid")
    mock_enrollment = mocker.Mock()
    mock_enrollment.role = "instructor"

    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_assignment,  # assignment_for_auth lookup
        mock_enrollment,  # enrollment auth lookup
    ]
    mock_query.return_value.filter_by.return_value.all.return_value = [
        Submission(id="sub-1"), Submission(id="sub-2")
    ]

    with client.session_transaction() as sess:
        sess["user_id"] = "instructor-uuid"

    resp = client.delete("/delete_submissions?assignment_id=assign-id")
    assert resp.status_code == 200
    assert "Submissions deleted successfully" in resp.json
    assert mock_delete.call_count == 2
    mock_commit.assert_called()


# ---------------------------------------------------------------------------
# assignment extensions
# ---------------------------------------------------------------------------

def test_create_extension_success(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        Assignment(id="assign-id", course_id="course-uuid"),  # auth lookup
        None,  # no existing extension
        AssignmentExtension(id="new-ext-id"),  # created extension re-fetch
    ]
    mock_add = mocker.patch("routes.assignment.db.session.add")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")
    _mock_course_role(mocker)
    login_as("instructor-uuid")

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


def test_create_extension_existing(client, mocker, login_as):
    with client.application.app_context():
        mock_query = mocker.patch("routes.assignment.db.session.query")
        mock_query.return_value.filter_by.return_value.first.side_effect = [
            Assignment(id="assign-id", course_id="course-uuid"),  # auth lookup
            AssignmentExtension(id="old-ext-id"),
            AssignmentExtension(id="new-ext-id"),  # created extension re-fetch
        ]

        mock_delete = mocker.patch("routes.assignment.db.session.delete")
        mock_commit = mocker.patch("routes.assignment.db.session.commit")
        _mock_course_role(mocker)
        login_as("instructor-uuid")

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


def test_delete_extension_found(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_ext = AssignmentExtension(id="ext-id", assignment_id="assign-id")
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_ext,
        Assignment(id="assign-id", course_id="course-uuid"),  # auth lookup
    ]
    mock_query.return_value.filter_by.return_value.all.return_value = []
    mock_delete = mocker.patch("routes.assignment.db.session.delete")
    mock_commit = mocker.patch("routes.assignment.db.session.commit")
    _mock_course_role(mocker)
    login_as("instructor-uuid")

    resp = client.delete("/delete_extension?extension_id=ext-id")
    assert resp.status_code == 200
    assert resp.json["message"] == "Extension deleted successfully"
    mock_delete.assert_called_with(mock_ext)
    mock_commit.assert_called()


def test_delete_extension_not_found(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None
    mock_query.return_value.filter_by.return_value.all.return_value = []
    login_as("instructor-uuid")

    resp = client.delete("/delete_extension?extension_id=notfound-id")
    assert resp.status_code == 404
    assert "Extension not found" in resp.json["message"]



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


# ---------------------------------------------------------------------------
# Negative-path auth tests (session-based guards)
# ---------------------------------------------------------------------------

def test_delete_assignment_unauthenticated(client):
    resp = client.delete("/delete_assignment?assignment_id=assign-id")
    assert resp.status_code == 401
    assert "Not authenticated" in resp.json["message"]


def test_delete_assignment_student_forbidden(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_assignment = Assignment(id="assign-id", course_id="course-uuid")
    mock_enrollment = mocker.Mock()
    mock_enrollment.role = "student"
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_assignment,
        mock_enrollment,
    ]
    with client.session_transaction() as sess:
        sess["user_id"] = "student-uuid"
    resp = client.delete("/delete_assignment?assignment_id=assign-id")
    assert resp.status_code == 403
    assert "Only instructors" in resp.json["message"]


def test_delete_submissions_unauthenticated(client):
    resp = client.delete("/delete_submissions?assignment_id=assign-id")
    assert resp.status_code == 401
    assert "Not authenticated" in resp.json["message"]


def test_delete_submissions_ta_forbidden(client, mocker):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_assignment = Assignment(id="assign-id", course_id="course-uuid")
    mock_enrollment = mocker.Mock()
    mock_enrollment.role = "ta"
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_assignment,
        mock_enrollment,
    ]
    with client.session_transaction() as sess:
        sess["user_id"] = "ta-uuid"
    resp = client.delete("/delete_submissions?assignment_id=assign-id")
    assert resp.status_code == 403
    assert "Only instructors" in resp.json["message"]


def test_delete_submissions_assignment_not_found(client, mocker):
    """Regression test: previously the auth check was skipped entirely when
    the assignment didn't exist, allowing submissions to be deleted with no
    authorization check at all."""
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_delete = mocker.patch("routes.assignment.db.session.delete")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    with client.session_transaction() as sess:
        sess["user_id"] = "student-uuid"

    resp = client.delete("/delete_submissions?assignment_id=notfound-id")
    assert resp.status_code == 404
    assert "Assignment not found" in resp.json["message"]
    mock_delete.assert_not_called()


def test_create_assignment_unauthenticated(client):
    resp = client.post("/create_assignment", json={
        "name": "New Assignment",
        "course_id": "course-uuid",
    })
    assert resp.status_code == 401
    assert "Not authenticated" in resp.json["message"]


def test_create_assignment_student_forbidden(client, mocker, login_as):
    _mock_course_role(mocker, role="student")
    login_as("student-uuid")

    resp = client.post("/create_assignment", json={
        "name": "New Assignment",
        "course_id": "course-uuid",
    })

    assert resp.status_code == 403
    assert "Only instructors or TAs" in resp.json["message"]


def test_create_assignment_ta_allowed(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.one_or_none.return_value = None
    mocker.patch("routes.assignment.db.session.add")
    mocker.patch("routes.assignment.db.session.commit")

    new_assignment = Assignment(id="123", name="New Assignment", course_id="course-uuid")
    mock_query.return_value.filter_by.return_value.first.return_value = new_assignment
    _mock_course_role(mocker, role="ta")
    login_as("ta-uuid")

    resp = client.post("/create_assignment", json={
        "name": "New Assignment",
        "course_id": "course-uuid",
    })

    assert resp.status_code == 200
    assert resp.json["id"] == "123"


def test_update_assignment_unauthenticated(client):
    resp = client.put("/update_assignment", json={
        "assignment_id": "some-uuid",
        "name": "Updated",
        "course_id": "course-uuid",
    })
    assert resp.status_code == 401
    assert "Not authenticated" in resp.json["message"]


def test_update_assignment_student_forbidden(client, mocker, login_as):
    _mock_course_role(mocker, role="student")
    login_as("student-uuid")

    resp = client.put("/update_assignment", json={
        "assignment_id": "some-uuid",
        "name": "Updated",
        "course_id": "course-uuid",
    })

    assert resp.status_code == 403
    assert "Only instructors or TAs" in resp.json["message"]


def test_duplicate_assignment_student_forbidden(client, mocker, login_as):
    _mock_course_role(mocker, role="student")
    login_as("student-uuid")

    resp = client.post("/duplicate_assignment", json={
        "oldAssignmentId": "old-id",
        "newAssignmentTitle": "New Title",
        "currentCourseId": "course-uuid",
    })

    assert resp.status_code == 403
    assert "Only instructors or TAs" in resp.json["message"]


def test_create_extension_unauthenticated(client):
    resp = client.post("/create_extension", json={
        "assignment_id": "assign-id",
        "student_id": "student-id",
    })
    assert resp.status_code == 401
    assert "Not authenticated" in resp.json["message"]


def test_create_extension_student_forbidden(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = Assignment(
        id="assign-id", course_id="course-uuid"
    )
    _mock_course_role(mocker, role="student")
    login_as("student-uuid")

    resp = client.post("/create_extension", json={
        "assignment_id": "assign-id",
        "student_id": "student-id",
    })

    assert resp.status_code == 403
    assert "Only instructors or TAs" in resp.json["message"]


def test_delete_extension_unauthenticated(client):
    resp = client.delete("/delete_extension?extension_id=ext-id")
    assert resp.status_code == 401
    assert "Not authenticated" in resp.json["message"]


def test_delete_extension_student_forbidden(client, mocker, login_as):
    mock_query = mocker.patch("routes.assignment.db.session.query")
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        AssignmentExtension(id="ext-id", assignment_id="assign-id"),
        Assignment(id="assign-id", course_id="course-uuid"),
    ]
    _mock_course_role(mocker, role="student")
    login_as("student-uuid")

    resp = client.delete("/delete_extension?extension_id=ext-id")

    assert resp.status_code == 403
    assert "Only instructors or TAs" in resp.json["message"]
