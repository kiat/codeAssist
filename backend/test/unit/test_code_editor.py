"""Tests for the code_editor routes."""
import pytest
from api import create_app, db
from api.models import CodeDraft, Assignment, Course


@pytest.fixture
def app():
    """Create a Flask app with the code_editor blueprint for testing."""
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client for sending requests."""
    return app.test_client()


# ---------------------------------------------------------------------------
# save_code_draft
# ---------------------------------------------------------------------------

def test_save_code_draft_success(client, mocker):
    mock_add = mocker.patch("routes.code_editor.db.session.add")
    mock_commit = mocker.patch("routes.code_editor.db.session.commit")
    mock_query = mocker.patch("routes.code_editor.db.session.query")
    # No existing drafts — version should be 1
    mock_query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None

    resp = client.post("/save_code_draft", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "content": "print('hello')",
        "file_name": "solution.py",
        "auto_saved": False,
    })

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["student_id"] == "stu-1"
    assert data["assignment_id"] == "asgn-1"
    assert data["content"] == "print('hello')"
    assert data["version_number"] == 1
    mock_add.assert_called_once()
    mock_commit.assert_called_once()


def test_save_code_draft_missing_fields(client):
    resp = client.post("/save_code_draft", json={
        "student_id": "stu-1",
        # missing assignment_id and content
    })
    assert resp.status_code == 400
    assert "Missing required fields" in resp.get_json()["message"]


def test_save_code_draft_content_too_long(client):
    resp = client.post("/save_code_draft", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "content": "x" * 100001,
    })
    assert resp.status_code == 400
    assert "maximum length" in resp.get_json()["message"].lower()


def test_save_code_draft_increments_version(client, mocker):
    mock_add = mocker.patch("routes.code_editor.db.session.add")
    mock_commit = mocker.patch("routes.code_editor.db.session.commit")
    mock_query = mocker.patch("routes.code_editor.db.session.query")

    # Simulate existing draft at version 3
    existing_draft = mocker.Mock()
    existing_draft.version_number = 3
    mock_query.return_value.filter_by.return_value.order_by.return_value.first.return_value = existing_draft

    resp = client.post("/save_code_draft", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "content": "print('v4')",
    })

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["version_number"] == 4


def test_save_code_draft_auto_saved_flag(client, mocker):
    mock_add = mocker.patch("routes.code_editor.db.session.add")
    mock_commit = mocker.patch("routes.code_editor.db.session.commit")
    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None

    resp = client.post("/save_code_draft", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "content": "x = 1",
        "auto_saved": True,
    })

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["auto_saved"] is True


# ---------------------------------------------------------------------------
# get_code_drafts
# ---------------------------------------------------------------------------

def test_get_code_drafts_success(client, mocker):
    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_schema = mocker.patch("routes.code_editor.CodeDraftSchema")

    fake_drafts = [{"id": "d1", "version_number": 1}]
    mock_query.return_value.filter_by.return_value.order_by.return_value.all.return_value = fake_drafts
    mock_schema.return_value.dump.return_value = fake_drafts

    resp = client.get("/get_code_drafts?student_id=stu-1&assignment_id=asgn-1")
    assert resp.status_code == 200
    assert resp.get_json() == fake_drafts


def test_get_code_drafts_missing_params(client):
    resp = client.get("/get_code_drafts")
    assert resp.status_code == 400
    assert "Missing" in resp.get_json()["message"]


def test_get_code_drafts_empty(client, mocker):
    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_schema = mocker.patch("routes.code_editor.CodeDraftSchema")
    mock_query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
    mock_schema.return_value.dump.return_value = []

    resp = client.get("/get_code_drafts?student_id=stu-1&assignment_id=asgn-1")
    assert resp.status_code == 200
    assert resp.get_json() == []


# ---------------------------------------------------------------------------
# get_latest_draft
# ---------------------------------------------------------------------------

def test_get_latest_draft_success(client, mocker):
    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_schema = mocker.patch("routes.code_editor.CodeDraftSchema")

    fake_draft = {"id": "d3", "content": "print('latest')", "version_number": 3}
    mock_query.return_value.filter_by.return_value.order_by.return_value.first.return_value = fake_draft
    mock_schema.return_value.dump.return_value = fake_draft

    resp = client.get("/get_latest_draft?student_id=stu-1&assignment_id=asgn-1")
    assert resp.status_code == 200
    assert resp.get_json()["content"] == "print('latest')"


def test_get_latest_draft_not_found(client, mocker):
    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None

    resp = client.get("/get_latest_draft?student_id=stu-1&assignment_id=asgn-1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "No drafts found"


def test_get_latest_draft_missing_params(client):
    resp = client.get("/get_latest_draft")
    assert resp.status_code == 400
    assert "Missing" in resp.get_json()["message"]


# ---------------------------------------------------------------------------
# submit_code
# ---------------------------------------------------------------------------

def test_submit_code_missing_fields(client):
    resp = client.post("/submit_code", json={
        "student_id": "stu-1",
        # missing assignment_id and content
    })
    assert resp.status_code == 400
    assert "Missing required fields" in resp.get_json()["message"]


def test_submit_code_content_too_long(client):
    resp = client.post("/submit_code", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "content": "x" * 100001,
    })
    assert resp.status_code == 400
    assert "maximum length" in resp.get_json()["message"].lower()


def test_submit_code_assignment_not_found(client, mocker):
    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    resp = client.post("/submit_code", json={
        "student_id": "stu-1",
        "assignment_id": "notfound",
        "content": "print('hi')",
    })
    assert resp.status_code == 404
    assert "not found" in resp.get_json()["message"].lower()


def test_submit_code_assignment_not_published(client, mocker):
    mock_assignment = mocker.Mock()
    mock_assignment.published = False

    mock_query = mocker.patch("routes.code_editor.db.session.query")
    # First call: assignment lookup
    mock_query.return_value.filter_by.return_value.first.return_value = mock_assignment

    resp = client.post("/submit_code", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "content": "print('hi')",
    })
    assert resp.status_code == 400
    assert "not published" in resp.get_json()["message"].lower()


def test_submit_code_past_due_date(client, mocker):
    from datetime import datetime, timezone, timedelta

    mock_assignment = mocker.Mock()
    mock_assignment.published = True
    mock_assignment.late_submission = False
    mock_assignment.published_date = None
    mock_assignment.due_date = datetime.now(timezone.utc) - timedelta(days=1)
    mock_assignment.late_due_date = None
    mock_assignment.autograder_image_name = ""
    mock_assignment.autograder_timeout = 300

    mock_extension = mocker.Mock()
    mock_extension.release_date_extension = None
    mock_extension.due_date_extension = None
    mock_extension.late_due_date_extension = None

    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_assignment,
        None,
    ]

    resp = client.post("/submit_code", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "content": "print('hi')",
    })
    assert resp.status_code == 400
    assert "past due date" in resp.get_json()["message"].lower()


# ---------------------------------------------------------------------------
# ai_chat
# ---------------------------------------------------------------------------

def test_ai_chat_missing_fields(client):
    resp = client.post("/ai_chat", json={
        "student_id": "stu-1",
        # missing message
    })
    assert resp.status_code == 400
    assert "Missing" in resp.get_json()["message"]


def test_ai_chat_missing_assignment(client):
    resp = client.post("/ai_chat", json={
        "student_id": "stu-1",
        "message": "help me",
        # missing assignment_id
    })
    assert resp.status_code == 400
    assert "Missing" in resp.get_json()["message"]


def test_ai_chat_assignment_not_found(client, mocker):
    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    resp = client.post("/ai_chat", json={
        "student_id": "stu-1",
        "assignment_id": "notfound",
        "message": "help me",
        "code": "print('hi')",
    })
    assert resp.status_code == 404
    assert "not found" in resp.get_json()["message"].lower()


def test_ai_chat_not_enabled(client, mocker):
    mock_assignment = mocker.Mock()
    mock_assignment.ai_feedback_enabled = False

    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = mock_assignment

    resp = client.post("/ai_chat", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "message": "help me",
        "code": "print('hi')",
    })
    assert resp.status_code == 400
    assert "not enabled" in resp.get_json()["message"].lower()


def test_ai_chat_no_api_key(client, mocker):
    mock_assignment = mocker.Mock()
    mock_assignment.ai_feedback_enabled = True
    mock_assignment.use_course_ai_default = True

    mock_course = mocker.Mock()
    mock_course.openai_api_key = ""
    mock_course.gemini_api_key = ""
    mock_course.claude_api_key = ""
    mock_course.ollama_base_url = ""
    mock_course.default_ai_provider = "openai"
    mock_course.default_ai_model = "gpt-4o-mini"

    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_assignment,  # assignment lookup
        mock_course,  # course lookup
    ]

    resp = client.post("/ai_chat", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "message": "help me",
        "code": "print('hi')",
    })
    assert resp.status_code == 400
    assert "not configured" in resp.get_json()["message"].lower()


def test_ai_chat_uses_custom_openai_provider_with_assignment_key(client, mocker):
    mock_assignment = mocker.Mock()
    mock_assignment.ai_feedback_enabled = True
    mock_assignment.course_id = "course-1"
    mock_assignment.use_course_ai_default = False
    mock_assignment.ai_feedback_provider = "openai"
    mock_assignment.ai_feedback_model = "gpt-4o-mini"
    mock_assignment.ai_feedback_temperature = 0.3
    mock_assignment.ai_feedback_api_key = "encrypted-assignment-openai-key"

    mock_course = mocker.Mock()
    mock_course.openai_api_key = ""
    mock_course.gemini_api_key = ""
    mock_course.claude_api_key = ""
    mock_course.ollama_base_url = ""
    mock_course.default_ai_provider = "gemini"
    mock_course.default_ai_model = "gemini-1.5-flash"

    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_assignment,
        mock_course,
    ]
    mocker.patch(
        "ai_feedback.integration.decrypt_api_key",
        return_value="decrypted-openai-key",
    )

    fake_client = mocker.Mock()
    fake_client.chat.completions.create.return_value = mocker.Mock(
        choices=[
            mocker.Mock(
                message=mocker.Mock(
                    content="Start by checking the accumulator update.",
                )
            )
        ]
    )
    mock_openai = mocker.patch(
        "ai_feedback.integration.OpenAI",
        return_value=fake_client,
    )

    resp = client.post("/ai_chat", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "message": "help me",
        "code": "print('hi')",
    })

    assert resp.status_code == 200
    assert resp.get_json()["reply"] == "Start by checking the accumulator update."
    mock_openai.assert_called_once_with(api_key="decrypted-openai-key")
    fake_client.chat.completions.create.assert_called_once()
    assert fake_client.chat.completions.create.call_args.kwargs["model"] == "gpt-4o-mini"


def test_ai_chat_uses_custom_gemini_provider_without_openai_key(client, mocker):
    mock_assignment = mocker.Mock()
    mock_assignment.ai_feedback_enabled = True
    mock_assignment.course_id = "course-1"
    mock_assignment.use_course_ai_default = False
    mock_assignment.ai_feedback_provider = "gemini"
    mock_assignment.ai_feedback_model = "gemini-1.5-flash"
    mock_assignment.ai_feedback_temperature = 0.4
    mock_assignment.ai_feedback_api_key = ""

    mock_course = mocker.Mock()
    mock_course.openai_api_key = ""
    mock_course.gemini_api_key = "encrypted-gemini-key"
    mock_course.claude_api_key = ""
    mock_course.ollama_base_url = ""
    mock_course.default_ai_provider = "openai"
    mock_course.default_ai_model = "gpt-4o-mini"

    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_assignment,
        mock_course,
    ]
    mocker.patch(
        "ai_feedback.integration.decrypt_api_key",
        return_value="decrypted-gemini-key",
    )

    fake_response = mocker.Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "Try checking the loop boundary first.",
                        }
                    ]
                }
            }
        ]
    }
    mock_post = mocker.patch("requests.post", return_value=fake_response)

    resp = client.post("/ai_chat", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "message": "help me",
        "code": "print('hi')",
    })

    assert resp.status_code == 200
    assert resp.get_json()["reply"] == "Try checking the loop boundary first."
    assert "gemini-1.5-flash:generateContent" in mock_post.call_args.args[0]
    assert mock_post.call_args.kwargs["params"]["key"] == "decrypted-gemini-key"


def test_ai_chat_uses_custom_claude_provider_without_openai_key(client, mocker):
    mock_assignment = mocker.Mock()
    mock_assignment.ai_feedback_enabled = True
    mock_assignment.course_id = "course-1"
    mock_assignment.use_course_ai_default = False
    mock_assignment.ai_feedback_provider = "claude"
    mock_assignment.ai_feedback_model = "claude-3-5-sonnet-20241022"
    mock_assignment.ai_feedback_temperature = 0.4
    mock_assignment.ai_feedback_api_key = ""

    mock_course = mocker.Mock()
    mock_course.openai_api_key = ""
    mock_course.gemini_api_key = ""
    mock_course.claude_api_key = "encrypted-claude-key"
    mock_course.ollama_base_url = ""
    mock_course.default_ai_provider = "openai"
    mock_course.default_ai_model = "gpt-4o-mini"

    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_assignment,
        mock_course,
    ]
    mocker.patch(
        "ai_feedback.integration.decrypt_api_key",
        return_value="decrypted-claude-key",
    )

    fake_response = mocker.Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "content": [
            {
                "type": "text",
                "text": "Look at the base case before changing the recursion.",
            }
        ]
    }
    mock_post = mocker.patch("requests.post", return_value=fake_response)

    resp = client.post("/ai_chat", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "message": "help me",
        "code": "print('hi')",
    })

    assert resp.status_code == 200
    assert resp.get_json()["reply"] == "Look at the base case before changing the recursion."
    assert mock_post.call_args.args[0] == "https://api.anthropic.com/v1/messages"
    assert mock_post.call_args.kwargs["headers"]["x-api-key"] == "decrypted-claude-key"
    assert (
        mock_post.call_args.kwargs["json"]["model"]
        == "claude-3-5-sonnet-20241022"
    )
