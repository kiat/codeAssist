"""Tests that verify the content passed to _get_ai_chat_reply includes
chat history (memory), assignment description, and coding_insights."""
import pytest
from api import create_app, db


@pytest.fixture
def app():
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _build_ai_chat_mocks(mocker, *, description="Build a calculator", insights="Struggles with loops", chat_history=None):
    """Helper to wire up the common mocks for a successful ai_chat call."""
    mock_assignment = mocker.Mock()
    mock_assignment.ai_feedback_enabled = True
    mock_assignment.course_id = "course-1"
    mock_assignment.use_course_ai_default = True
    mock_assignment.description = description
    mock_assignment.ai_feedback_temperature = None

    mock_course = mocker.Mock()
    mock_course.openai_api_key = "encrypted-key"
    mock_course.gemini_api_key = ""
    mock_course.claude_api_key = ""
    mock_course.ollama_base_url = ""
    mock_course.default_ai_provider = "openai"
    mock_course.default_ai_model = "gpt-4o-mini"
    mock_course.default_ai_temperature = 0.5

    mock_student = mocker.Mock()
    mock_student.id = "stu-1"
    mock_student.coding_insights = insights

    mocker.patch("routes.code_editor._verify_student", return_value=mock_student)
    mocker.patch("routes.code_editor._verify_enrollment")
    mocker.patch(
        "routes.code_editor.check_feedback_limits",
        return_value={"allowed": True, "remaining": None, "wait_seconds": 0, "message": ""},
    )
    mocker.patch("routes.code_editor.get_student_feedback_status", return_value={"remaining": 5, "wait_seconds": 0})
    mocker.patch("routes.code_editor.store_chat_message")
    mocker.patch("routes.code_editor.record_feedback_request")
    mocker.patch("routes.code_editor.get_chat_history", return_value=chat_history or [])
    mocker.patch("ai_feedback.integration.decrypt_api_key", return_value="decrypted-key")

    mock_query = mocker.patch("routes.code_editor.db.session.query")
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_assignment,  # assignment lookup
        mock_course,      # course lookup
    ]

    return mock_assignment, mock_course, mock_student


def test_ai_chat_prompt_includes_chat_history(client, mocker):
    """get_chat_history is called and its output appears in the prompt sent to the LLM."""
    fake_history = [
        {"role": "user", "content": "Why does my loop skip the first element?"},
        {"role": "assistant", "content": "Check your range start index."},
    ]

    _build_ai_chat_mocks(mocker, chat_history=fake_history)
    mock_reply = mocker.patch("routes.code_editor._get_ai_chat_reply", return_value="Try index 0.")

    resp = client.post("/ai_chat", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "message": "I still have the bug",
        "code": "for i in range(1, len(arr)): print(arr[i])",
    })

    assert resp.status_code == 200
    mock_reply.assert_called_once()
    prompt_arg = mock_reply.call_args.kwargs.get("user_prompt") or mock_reply.call_args.args[3]

    assert "Why does my loop skip the first element?" in prompt_arg
    assert "Check your range start index." in prompt_arg
    assert "Previous conversation:" in prompt_arg


def test_ai_chat_prompt_includes_assignment_description(client, mocker):
    """Assignment description is included in the prompt sent to the LLM."""
    _build_ai_chat_mocks(mocker, description="Write a function that computes the factorial of n")
    mock_reply = mocker.patch("routes.code_editor._get_ai_chat_reply", return_value="Hint: think recursion.")

    resp = client.post("/ai_chat", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "message": "How do I start?",
        "code": "def factorial(n): pass",
    })

    assert resp.status_code == 200
    prompt_arg = mock_reply.call_args.kwargs.get("user_prompt") or mock_reply.call_args.args[3]

    assert "factorial" in prompt_arg.lower()
    assert "Assignment description:" in prompt_arg


def test_ai_chat_prompt_includes_coding_insights(client, mocker):
    """Student coding_insights (memory) is included in the prompt sent to the LLM."""
    _build_ai_chat_mocks(mocker, insights="Struggles with off-by-one errors in loops")
    mock_reply = mocker.patch("routes.code_editor._get_ai_chat_reply", return_value="Watch your range bounds.")

    resp = client.post("/ai_chat", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "message": "My loop is wrong",
        "code": "for i in range(len(arr)+1): print(arr[i])",
    })

    assert resp.status_code == 200
    prompt_arg = mock_reply.call_args.kwargs.get("user_prompt") or mock_reply.call_args.args[3]

    assert "off-by-one" in prompt_arg
    assert "Student coding history:" in prompt_arg


def test_ai_chat_prompt_excludes_empty_insights(client, mocker):
    """When coding_insights is 'No history.', it should not clutter the prompt."""
    _build_ai_chat_mocks(mocker, insights="No history.")
    mock_reply = mocker.patch("routes.code_editor._get_ai_chat_reply", return_value="Sure, let's begin.")

    resp = client.post("/ai_chat", json={
        "student_id": "stu-1",
        "assignment_id": "asgn-1",
        "message": "Hello",
        "code": "print('hi')",
    })

    assert resp.status_code == 200
    prompt_arg = mock_reply.call_args.kwargs.get("user_prompt") or mock_reply.call_args.args[3]

    assert "No history." not in prompt_arg
    assert "Student coding history:" not in prompt_arg
