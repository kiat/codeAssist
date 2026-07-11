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


def test_get_assignment_ai_settings_returns_usage_limits(client, mocker, login_as):
    mock_assignment = Assignment(
        id="assignment-uuid",
        name="AI Assignment",
        course_id="course-uuid",
        ai_feedback_max_requests=10,
        ai_feedback_wait_seconds=300,
    )
    _mock_ai_settings_queries(mocker, assignment=mock_assignment)
    login_as("instructor-uuid")

    resp = client.get("/assignments/assignment-uuid/ai-settings")

    assert resp.status_code == 200
    assert set(resp.json.keys()) == EXPECTED_AI_SETTINGS_KEYS
    assert "feedback_prompts" not in resp.json
    assert "allowed_inputs" not in resp.json
    assert resp.json["ai_feedback_prompts"][0]["id"] == "check_correctness"
    assert resp.json["ai_allowed_inputs"]["student_code"] is True
    assert resp.json["ai_feedback_max_requests"] == 10
    assert resp.json["ai_feedback_wait_seconds"] == 300


def test_ta_can_get_assignment_ai_settings(client, mocker, login_as):
    _mock_ai_settings_queries(
        mocker,
        enrollment=Enrollment(
            student_id="ta-uuid",
            course_id="course-uuid",
            role="ta",
        ),
    )
    login_as("ta-uuid")

    resp = client.get("/assignments/assignment-uuid/ai-settings")

    assert resp.status_code == 200
    assert set(resp.json.keys()) == EXPECTED_AI_SETTINGS_KEYS


@pytest.mark.parametrize("method", ["get", "put"])
def test_assignment_ai_settings_requires_authentication(client, mocker, method):
    _mock_ai_settings_queries(mocker)

    if method == "get":
        resp = client.get("/assignments/assignment-uuid/ai-settings")
    else:
        resp = client.put("/assignments/assignment-uuid/ai-settings", json={})

    assert resp.status_code == 401
    assert "Not authenticated" in resp.json["message"]


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
    login_as,
):
    _mock_ai_settings_queries(mocker, enrollment=enrollment)
    login_as(requester_id)

    resp = client.get("/assignments/assignment-uuid/ai-settings")

    assert resp.status_code == 403
    assert "Only instructors or TAs" in resp.json["message"]


def test_spoofed_requester_id_is_ignored(client, mocker, login_as):
    """A student cannot impersonate the instructor by passing requester_id."""
    _mock_ai_settings_queries(
        mocker,
        enrollment=Enrollment(
            student_id="student-uuid",
            course_id="course-uuid",
            role="student",
        ),
    )
    login_as("student-uuid")

    resp = client.get(
        "/assignments/assignment-uuid/ai-settings",
        query_string={"requester_id": "instructor-uuid"},
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
    login_as,
):
    _mock_ai_settings_queries(
        mocker,
        enrollment=enrollment,
    )
    mock_commit = mocker.patch("routes.ai_feedback.db.session.commit")
    login_as(requester_id)

    resp = client.put(
        "/assignments/assignment-uuid/ai-settings",
        json={"ai_feedback_wait_seconds": 60},
    )

    assert resp.status_code == 403
    assert "Only instructors or TAs" in resp.json["message"]
    mock_commit.assert_not_called()


def test_update_assignment_ai_settings_saves_usage_limits(client, mocker, login_as):
    mock_assignment = _mock_ai_settings_queries(mocker)
    mock_commit = mocker.patch("routes.ai_feedback.db.session.commit")
    login_as("instructor-uuid")

    resp = client.put(
        "/assignments/assignment-uuid/ai-settings",
        json={
            "ai_feedback_max_requests": 0,
            "ai_feedback_wait_seconds": 60,
        },
    )

    assert resp.status_code == 200
    assert mock_assignment.ai_feedback_max_requests == 0
    assert mock_assignment.ai_feedback_wait_seconds == 60
    mock_commit.assert_called_once()


def test_update_assignment_ai_settings_saves_assignment_api_key(client, mocker, login_as):
    mock_assignment = _mock_ai_settings_queries(mocker)
    mock_encrypt = mocker.patch(
        "ai_feedback.settings.encrypt_api_key",
        return_value="encrypted-assignment-key",
    )
    mock_commit = mocker.patch("routes.ai_feedback.db.session.commit")
    login_as("instructor-uuid")

    resp = client.put(
        "/assignments/assignment-uuid/ai-settings",
        json={
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
    login_as,
):
    _mock_ai_settings_queries(mocker)
    mock_rollback = mocker.patch("routes.ai_feedback.db.session.rollback")
    login_as("instructor-uuid")

    resp = client.put("/assignments/assignment-uuid/ai-settings", json=payload)

    assert resp.status_code == 400
    assert message in resp.json["message"]
    mock_rollback.assert_called_once()
