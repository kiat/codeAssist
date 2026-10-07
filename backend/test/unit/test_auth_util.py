import pytest
from flask import session

from api import create_app
from api.models import Enrollment, User
from util.auth import (
    get_user_course_role,
    get_user_global_role,
    require_admin,
    require_authenticated,
    require_course_role,
    require_self_or_admin,
)
from util.errors import ForbiddenError, UnauthorizedError


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


def test_get_user_course_role_returns_none_when_enrollment_role_is_none(app, mocker):
    mock_query = mocker.patch("util.auth.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = Enrollment(
        student_id="user-123", course_id="course-123", role=None,
    )

    role = get_user_course_role("user-123", "course-123")

    assert role is None


def test_require_authenticated_raises_401_without_session(app):
    with app.test_request_context("/"):
        with pytest.raises(UnauthorizedError):
            require_authenticated()


def test_require_authenticated_returns_user_id(app):
    with app.test_request_context("/"):
        session["user_id"] = "user-123"
        assert require_authenticated() == "user-123"


def test_require_course_role_raises_401_without_session(app):
    with app.test_request_context("/"):
        with pytest.raises(UnauthorizedError):
            require_course_role("course-123", {"instructor"}, "nope")


def test_require_course_role_raises_403_for_disallowed_role(app, mocker):
    mocker.patch("util.auth.get_user_course_role", return_value="student")

    with app.test_request_context("/"):
        session["user_id"] = "user-123"
        with pytest.raises(ForbiddenError, match="Only instructors"):
            require_course_role("course-123", {"instructor"}, "Only instructors")


def test_require_course_role_raises_403_when_not_enrolled(app, mocker):
    mocker.patch("util.auth.get_user_course_role", return_value=None)

    with app.test_request_context("/"):
        session["user_id"] = "user-123"
        with pytest.raises(ForbiddenError):
            require_course_role("course-123", {"student", "ta", "instructor"}, "nope")


def test_require_course_role_returns_user_and_role_when_allowed(app, mocker):
    mocker.patch("util.auth.get_user_course_role", return_value="ta")

    with app.test_request_context("/"):
        session["user_id"] = "user-123"
        user_id, role = require_course_role("course-123", {"instructor", "ta"}, "nope")

    assert user_id == "user-123"
    assert role == "ta"


def test_get_user_course_role_caches_within_a_request(app, mocker):
    mock_query = mocker.patch("util.auth.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = Enrollment(
        student_id="user-123", course_id="course-123", role="ta",
    )

    with app.test_request_context("/"):
        first = get_user_course_role("user-123", "course-123")
        second = get_user_course_role("user-123", "course-123")

    assert first == second == "ta"
    mock_query.assert_called_once()


def test_get_user_course_role_cache_does_not_leak_across_requests(app, mocker):
    # Uses app.app_context() rather than test_request_context(): the
    # latter reuses whatever app context is already on the stack (here,
    # the one the `app` fixture leaves pushed for the whole test), so it
    # wouldn't actually give each block a fresh `g` the way two separate
    # real HTTP requests would.
    mock_query = mocker.patch("util.auth.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = Enrollment(
        student_id="user-123", course_id="course-123", role="student",
    )

    with app.app_context():
        first = get_user_course_role("user-123", "course-123")

    mock_query.return_value.filter_by.return_value.first.return_value = Enrollment(
        student_id="user-123", course_id="course-123", role="instructor",
    )

    with app.app_context():
        second = get_user_course_role("user-123", "course-123")

    assert first == "student"
    assert second == "instructor"
    assert mock_query.call_count == 2


def test_get_user_global_role_lowercases_stored_role(app, mocker):
    mock_query = mocker.patch("util.auth.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = User(
        id="user-123", role="Admin",
    )

    with app.app_context():
        assert get_user_global_role("user-123") == "admin"


def test_get_user_global_role_returns_none_for_missing_user(app, mocker):
    mock_query = mocker.patch("util.auth.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    with app.app_context():
        assert get_user_global_role("user-123") is None


def test_require_admin_raises_401_without_session(app):
    with app.test_request_context("/"):
        with pytest.raises(UnauthorizedError):
            require_admin()


@pytest.mark.parametrize("role", ["student", "instructor", None])
def test_require_admin_raises_403_for_non_admin(app, mocker, role):
    mocker.patch("util.auth.get_user_global_role", return_value=role)

    with app.test_request_context("/"):
        session["user_id"] = "user-123"
        with pytest.raises(ForbiddenError, match="Admins only"):
            require_admin("Admins only")


def test_require_admin_returns_user_id_for_admin(app, mocker):
    mocker.patch("util.auth.get_user_global_role", return_value="admin")

    with app.test_request_context("/"):
        session["user_id"] = "admin-123"
        assert require_admin() == "admin-123"


def test_require_self_or_admin_raises_401_without_session(app):
    with app.test_request_context("/"):
        with pytest.raises(UnauthorizedError):
            require_self_or_admin("user-123")


def test_require_self_or_admin_allows_self_without_role_lookup(app, mocker):
    mock_role = mocker.patch("util.auth.get_user_global_role")

    with app.test_request_context("/"):
        session["user_id"] = "user-123"
        assert require_self_or_admin("user-123") == "user-123"

    mock_role.assert_not_called()


def test_require_self_or_admin_raises_403_for_other_non_admin(app, mocker):
    mocker.patch("util.auth.get_user_global_role", return_value="student")

    with app.test_request_context("/"):
        session["user_id"] = "user-123"
        with pytest.raises(ForbiddenError):
            require_self_or_admin("someone-else")


def test_require_self_or_admin_allows_admin_for_other_user(app, mocker):
    mocker.patch("util.auth.get_user_global_role", return_value="admin")

    with app.test_request_context("/"):
        session["user_id"] = "admin-123"
        assert require_self_or_admin("someone-else") == "admin-123"
