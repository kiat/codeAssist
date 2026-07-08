import pytest

from api import create_app
from api.models import Enrollment
from util.auth import get_user_course_role


@pytest.fixture
def app():
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        yield app


def test_get_user_course_role_lowercases_stored_role(app, mocker):
    mock_query = mocker.patch("util.auth.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = Enrollment(
        student_id="user-123", course_id="course-123", role="Instructor",
    )

    role = get_user_course_role("user-123", "course-123")

    assert role == "instructor"


def test_get_user_course_role_returns_none_when_not_enrolled(app, mocker):
    mock_query = mocker.patch("util.auth.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    role = get_user_course_role("user-123", "course-123")

    assert role is None
