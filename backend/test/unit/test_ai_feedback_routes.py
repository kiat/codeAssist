import pytest

from api import create_app
from api.models import Assignment, Course, Enrollment


EXPECTED_AI_SETTINGS_KEYS = {
    "ai_feedback_enabled",
    "use_course_ai_default",
    "ai_feedback_provider",
    "ai_feedback_model",
    "ai_feedback_temperature",
    "ai_feedback_style",
    "ai_feedback_max_requests",
    "ai_feedback_wait_seconds",
    "ai_feedback_prompts",
    "ai_allowed_inputs",
    "has_assignment_ai_key",
}


@pytest.fixture
def app():
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


def _mock_ai_settings_queries(
    mocker,
    assignment=None,
    course=None,
    enrollment=None,
):
    assignment = assignment or Assignment(
        id="assignment-uuid",
        name="AI Assignment",
        course_id="course-uuid",
    )
    course = course or Course(
        id=assignment.course_id,
        instructor_id="instructor-uuid",
    )

    assignment_query = mocker.Mock()
    assignment_query.filter_by.return_value.first.return_value = assignment

    course_query = mocker.Mock()
    course_query.filter_by.return_value.first.return_value = course

    enrollment_query = mocker.Mock()
    enrollment_query.filter_by.return_value.first.return_value = enrollment

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

    return assignment


def test_get_assignment_ai_settings_returns_usage_limits(client, mocker):
    mock_assignment = Assignment(
        id="assignment-uuid",
        name="AI Assignment",
        course_id="course-uuid",
        ai_feedback_max_requests=10,
        ai_feedback_wait_seconds=300,
    )
    _mock_ai_settings_queries(mocker, assignment=mock_assignment)

    resp = client.get(
        "/assignments/assignment-uuid/ai-settings",
        query_string={"requester_id": "instructor-uuid"},
    )

    assert resp.status_code == 200
    assert set(resp.json.keys()) == EXPECTED_AI_SETTINGS_KEYS
    assert "feedback_prompts" not in resp.json
    assert "allowed_inputs" not in resp.json
    assert resp.json["ai_feedback_prompts"][0]["id"] == "check_correctness"
    assert resp.json["ai_allowed_inputs"]["student_code"] is True
    assert resp.json["ai_feedback_max_requests"] == 10
    assert resp.json["ai_feedback_wait_seconds"] == 300


def test_ta_can_get_assignment_ai_settings(client, mocker):
    _mock_ai_settings_queries(
        mocker,
        enrollment=Enrollment(
            student_id="ta-uuid",
            course_id="course-uuid",
            role="ta",
        ),
    )

    resp = client.get(
        "/assignments/assignment-uuid/ai-settings",
        query_string={"requester_id": "ta-uuid"},
    )

    assert resp.status_code == 200
    assert set(resp.json.keys()) == EXPECTED_AI_SETTINGS_KEYS


@pytest.mark.parametrize("method", ["get", "put"])
def test_assignment_ai_settings_requires_requester_id(client, mocker, method):
    _mock_ai_settings_queries(mocker)

    if method == "get":
        resp = client.get("/assignments/assignment-uuid/ai-settings")
    else:
        resp = client.put("/assignments/assignment-uuid/ai-settings", json={})

    assert resp.status_code == 403
    assert "Missing requester_id" in resp.json["message"]


@pytest.mark.parametrize(
    "requester_id, enrollment",
    [
        (
            "student-uuid",
            Enrollment(
                student_id="student-uuid",
                course_id="course-uuid",
                role="student",
            ),
        ),
        ("unrelated-uuid", None),
    ],
)
def test_non_instructor_or_ta_cannot_get_assignment_ai_settings(
    client,
    mocker,
    requester_id,
    enrollment,
):
    _mock_ai_settings_queries(mocker, enrollment=enrollment)

    resp = client.get(
        "/assignments/assignment-uuid/ai-settings",
        query_string={"requester_id": requester_id},
    )

    assert resp.status_code == 403
    assert "Only instructors or TAs" in resp.json["message"]


@pytest.mark.parametrize(
    "requester_id, enrollment",
    [
        (
            "student-uuid",
            Enrollment(
                student_id="student-uuid",
                course_id="course-uuid",
                role="student",
            ),
        ),
        ("unrelated-uuid", None),
    ],
)
def test_non_instructor_or_ta_cannot_update_assignment_ai_settings(
    client,
    mocker,
    requester_id,
    enrollment,
):
    _mock_ai_settings_queries(
        mocker,
        enrollment=enrollment,
    )
    mock_commit = mocker.patch("routes.ai_feedback.db.session.commit")

    resp = client.put(
        "/assignments/assignment-uuid/ai-settings",
        json={
            "requester_id": requester_id,
            "ai_feedback_wait_seconds": 60,
        },
    )

    assert resp.status_code == 403
    assert "Only instructors or TAs" in resp.json["message"]
    mock_commit.assert_not_called()


def test_update_assignment_ai_settings_saves_usage_limits(client, mocker):
    mock_assignment = _mock_ai_settings_queries(mocker)
    mock_commit = mocker.patch("routes.ai_feedback.db.session.commit")

    resp = client.put(
        "/assignments/assignment-uuid/ai-settings",
        json={
            "requester_id": "instructor-uuid",
            "ai_feedback_max_requests": 0,
            "ai_feedback_wait_seconds": 60,
        },
    )

    assert resp.status_code == 200
    assert mock_assignment.ai_feedback_max_requests == 0
    assert mock_assignment.ai_feedback_wait_seconds == 60
    mock_commit.assert_called_once()


def test_update_assignment_ai_settings_saves_assignment_api_key(client, mocker):
    mock_assignment = _mock_ai_settings_queries(mocker)
    mock_encrypt = mocker.patch(
        "ai_feedback.settings.encrypt_api_key",
        return_value="encrypted-assignment-key",
    )
    mock_commit = mocker.patch("routes.ai_feedback.db.session.commit")

    resp = client.put(
        "/assignments/assignment-uuid/ai-settings",
        json={
            "requester_id": "instructor-uuid",
            "use_course_ai_default": False,
            "ai_feedback_provider": "gemini",
            "ai_feedback_model": "gemini-1.5-flash",
            "ai_feedback_api_key": "plain-assignment-key",
        },
    )

    assert resp.status_code == 200
    assert mock_assignment.ai_feedback_api_key == "encrypted-assignment-key"
    mock_encrypt.assert_called_once_with("plain-assignment-key")
    mock_commit.assert_called_once()


@pytest.mark.parametrize(
    "payload, message",
    [
        (
            {"ai_feedback_max_requests": -1},
            "ai_feedback_max_requests must be a non-negative integer",
        ),
        (
            {"ai_feedback_max_requests": "3"},
            "ai_feedback_max_requests must be a non-negative integer",
        ),
        (
            {"ai_feedback_max_requests": True},
            "ai_feedback_max_requests must be a non-negative integer",
        ),
        (
            {"ai_feedback_max_requests": 1001},
            "ai_feedback_max_requests must be less than or equal to 1000",
        ),
        (
            {"ai_feedback_wait_seconds": -1},
            "ai_feedback_wait_seconds must be a non-negative integer",
        ),
        (
            {"ai_feedback_wait_seconds": "60"},
            "ai_feedback_wait_seconds must be a non-negative integer",
        ),
        (
            {"ai_feedback_wait_seconds": False},
            "ai_feedback_wait_seconds must be a non-negative integer",
        ),
    ],
)
def test_update_assignment_ai_settings_rejects_invalid_usage_limits(
    client,
    mocker,
    payload,
    message,
):
    _mock_ai_settings_queries(mocker)
    mock_rollback = mocker.patch("routes.ai_feedback.db.session.rollback")
    payload = {"requester_id": "instructor-uuid", **payload}

    resp = client.put("/assignments/assignment-uuid/ai-settings", json=payload)

    assert resp.status_code == 400
    assert message in resp.json["message"]
    mock_rollback.assert_called_once()


# --- Tests for GET /assignments/<id>/prompts ---


def test_get_prompts_returns_enabled_prompts(client, mocker):
    mock_assignment = Assignment(
        id="assignment-uuid",
        name="AI Assignment",
        course_id="course-uuid",
        ai_feedback_enabled=True,
        ai_feedback_prompts=[
            {"id": "p1", "title": "Debug", "prompt": "Help debug", "enabled": True},
            {"id": "p2", "title": "Explain", "prompt": "Explain code", "enabled": False},
        ],
    )
    _mock_ai_settings_queries(
        mocker,
        assignment=mock_assignment,
        enrollment=Enrollment(student_id="stu-uuid", course_id="course-uuid", role="student"),
    )

    with client.session_transaction() as sess:
        sess["user_id"] = "stu-uuid"

    resp = client.get(
        "/assignments/assignment-uuid/prompts",
        query_string={"student_id": "stu-uuid"},
    )

    assert resp.status_code == 200
    assert resp.json["ai_feedback_enabled"] is True
    assert len(resp.json["ai_feedback_prompts"]) == 1
    assert resp.json["ai_feedback_prompts"][0]["id"] == "p1"


def test_get_prompts_rejects_unauthenticated(client, mocker):
    _mock_ai_settings_queries(mocker)

    resp = client.get(
        "/assignments/assignment-uuid/prompts",
        query_string={"student_id": "stu-uuid"},
    )

    assert resp.status_code == 403
    assert "Not authenticated" in resp.json["message"]


def test_get_prompts_rejects_session_mismatch(client, mocker):
    _mock_ai_settings_queries(mocker)

    with client.session_transaction() as sess:
        sess["user_id"] = "other-stu-uuid"

    resp = client.get(
        "/assignments/assignment-uuid/prompts",
        query_string={"student_id": "stu-uuid"},
    )

    assert resp.status_code == 403
    assert "You can only access your own data" in resp.json["message"]


def test_get_prompts_rejects_unenrolled_student(client, mocker):
    _mock_ai_settings_queries(mocker, enrollment=None)

    with client.session_transaction() as sess:
        sess["user_id"] = "stu-uuid"

    resp = client.get(
        "/assignments/assignment-uuid/prompts",
        query_string={"student_id": "stu-uuid"},
    )

    assert resp.status_code == 403
    assert "not enrolled" in resp.json["message"]


# --- Tests for GET /ai_feedback_status ---


def test_get_ai_feedback_status_returns_status(client, mocker):
    mock_assignment = Assignment(
        id="assignment-uuid",
        name="AI Assignment",
        course_id="course-uuid",
        ai_feedback_enabled=True,
        ai_feedback_max_requests=10,
    )
    _mock_ai_settings_queries(
        mocker,
        assignment=mock_assignment,
        enrollment=Enrollment(student_id="stu-uuid", course_id="course-uuid", role="student"),
    )
    # Mock _verify_student to avoid DB query for User model
    mock_user = mocker.Mock()
    mock_user.id = "stu-uuid"
    mocker.patch("routes.code_editor._verify_student", return_value=mock_user)
    mocker.patch("routes.code_editor._verify_enrollment")
    mocker.patch("routes.code_editor.get_student_feedback_status", return_value={"remaining": 5, "wait_seconds": 0})

    with client.session_transaction() as sess:
        sess["user_id"] = "stu-uuid"

    resp = client.get(
        "/ai_feedback_status",
        query_string={"student_id": "stu-uuid", "assignment_id": "assignment-uuid"},
    )

    assert resp.status_code == 200
    assert resp.json["ai_feedback_enabled"] is True
    assert "remaining" in resp.json


def test_get_ai_feedback_status_when_disabled(client, mocker):
    mock_assignment = Assignment(
        id="assignment-uuid",
        course_id="course-uuid",
        ai_feedback_enabled=False,
    )
    _mock_ai_settings_queries(mocker, assignment=mock_assignment)
    # Mock _verify_student to avoid DB query for User model
    mock_user = mocker.Mock()
    mock_user.id = "stu-uuid"
    mocker.patch("routes.code_editor._verify_student", return_value=mock_user)

    with client.session_transaction() as sess:
        sess["user_id"] = "stu-uuid"

    resp = client.get(
        "/ai_feedback_status",
        query_string={"student_id": "stu-uuid", "assignment_id": "assignment-uuid"},
    )

    assert resp.status_code == 200
    assert resp.json["ai_feedback_enabled"] is False
    assert resp.json["remaining"] == 0


def test_get_ai_feedback_status_rejects_unauthenticated(client, mocker):
    _mock_ai_settings_queries(mocker)

    resp = client.get(
        "/ai_feedback_status",
        query_string={"student_id": "stu-uuid", "assignment_id": "assignment-uuid"},
    )

    assert resp.status_code == 403
    assert "Not authenticated" in resp.json["message"]
