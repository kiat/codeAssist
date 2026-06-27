import pytest

from api import create_app
from api.models import Assignment


@pytest.fixture
def app():
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_get_assignment_ai_settings_returns_usage_limits(client, mocker):
    mock_query = mocker.patch("routes.ai_feedback.db.session.query")
    mock_assignment = Assignment(
        id="assignment-uuid",
        name="AI Assignment",
        ai_feedback_max_requests=10,
        ai_feedback_wait_seconds=300,
    )
    mock_query.return_value.filter_by.return_value.first.return_value = mock_assignment

    resp = client.get("/assignments/assignment-uuid/ai-settings")

    assert resp.status_code == 200
    assert "feedback_prompts" not in resp.json
    assert "allowed_inputs" not in resp.json
    assert resp.json["ai_feedback_prompts"][0]["id"] == "check_correctness"
    assert resp.json["ai_allowed_inputs"]["student_code"] is True
    assert resp.json["ai_feedback_max_requests"] == 10
    assert resp.json["ai_feedback_wait_seconds"] == 300


def test_update_assignment_ai_settings_saves_usage_limits(client, mocker):
    mock_query = mocker.patch("routes.ai_feedback.db.session.query")
    mock_assignment = Assignment(id="assignment-uuid", name="AI Assignment")
    mock_query.return_value.filter_by.return_value.first.return_value = mock_assignment
    mock_commit = mocker.patch("routes.ai_feedback.db.session.commit")

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
    mock_query = mocker.patch("routes.ai_feedback.db.session.query")
    mock_assignment = Assignment(id="assignment-uuid", name="AI Assignment")
    mock_query.return_value.filter_by.return_value.first.return_value = mock_assignment
    mock_rollback = mocker.patch("routes.ai_feedback.db.session.rollback")

    resp = client.put("/assignments/assignment-uuid/ai-settings", json=payload)

    assert resp.status_code == 400
    assert message in resp.json["message"]
    mock_rollback.assert_called_once()
