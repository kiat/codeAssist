import uuid

import pytest

from api import create_app, db
from api.models import User


@pytest.fixture
def app():
    app = create_app("config.TestConfig")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _user(role="student"):
    user = User(
        id=str(uuid.uuid4()),
        name="Pat",
        email_address="pat@example.com",
        password="x",
        sis_user_id="pat1",
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_set_role_promotes_account(app):
    user = _user()
    result = app.test_cli_runner().invoke(args=["set-role", "pat@example.com", "admin"])
    assert result.exit_code == 0, result.output
    assert "student -> admin" in result.output
    db.session.refresh(user)
    assert user.role == "admin"


def test_set_role_unknown_email_fails(app):
    result = app.test_cli_runner().invoke(args=["set-role", "nobody@example.com", "admin"])
    assert result.exit_code != 0
    assert "No account" in result.output


def test_set_role_rejects_bad_role(app):
    _user()
    result = app.test_cli_runner().invoke(args=["set-role", "pat@example.com", "ta"])
    assert result.exit_code != 0
