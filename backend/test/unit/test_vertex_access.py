"""Gemini over Vertex AI spends the deployment's credits, so an admin must
enable it per course, and only instructors can point an assignment at it."""
import pytest

from api import create_app, db
from api.models import Assignment, Course, Enrollment, User


COURSE_ID = "c0a8e1f2-3b4d-4e5f-8a9b-0c1d2e3f4a5b"
ASSIGNMENT_ID = "a1b2c3d4-e5f6-4a7b-8c9d-e0f1a2b3c4d5"
ADMIN_ID = "ad0a1b2c-3d4e-4f5a-9b6c-7d8e9f0a1b2c"
INSTRUCTOR_ID = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"
TA_ID = "fa0b1c2d-3e4f-4a5b-8c6d-7e8f9a0b1c2d"


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("VERTEX_AI_AUTH_MODE", "api_key")
    monkeypatch.setenv("VERTEX_AI_API_KEY", "test-vertex-key")
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _user(user_id, role):
    return User(
        id=user_id,
        password="x",
        name=role,
        email_address=f"{user_id}@example.com",
        sis_user_id=user_id,
        role=role,
    )


@pytest.fixture
def course(app):
    db.session.add_all([
        _user(ADMIN_ID, "admin"),
        _user(INSTRUCTOR_ID, "instructor"),
        _user(TA_ID, "student"),
    ])
    course = Course(
        id=COURSE_ID,
        name="CS 101",
        instructor_id=INSTRUCTOR_ID,
        semester="Fall",
        year="2026",
        entryCode="ENTRY1",
    )
    db.session.add(course)
    db.session.add_all([
        Enrollment(student_id=INSTRUCTOR_ID, course_id=COURSE_ID, role="instructor"),
        Enrollment(student_id=TA_ID, course_id=COURSE_ID, role="ta"),
    ])
    db.session.add(Assignment(id=ASSIGNMENT_ID, name="HW1", course_id=COURSE_ID))
    db.session.commit()
    return course


def _enable_vertex(enabled=True):
    course = db.session.get(Course, COURSE_ID)
    course.vertex_enabled = enabled
    db.session.commit()


def _vertex_override(**extra):
    return {
        "use_course_ai_default": False,
        "ai_feedback_provider": "gemini_vertex",
        "ai_feedback_model": "gemini-2.5-flash",
        **extra,
    }


def _put_ai_settings(client, payload):
    return client.put(f"/assignments/{ASSIGNMENT_ID}/ai-settings", json=payload)


# -- Admin toggle -----------------------------------------------------------

def test_new_course_has_vertex_disabled(course):
    assert db.session.get(Course, COURSE_ID).vertex_enabled is False


def test_admin_can_enable_and_disable_vertex(client, course, login_as):
    login_as(ADMIN_ID)

    response = client.put(
        "/admin_set_course_vertex", json={"course_id": COURSE_ID, "enabled": True}
    )
    assert response.status_code == 200
    assert response.json == {"course_id": COURSE_ID, "vertex_enabled": True}
    assert db.session.get(Course, COURSE_ID).vertex_enabled is True

    response = client.put(
        "/admin_set_course_vertex", json={"course_id": COURSE_ID, "enabled": False}
    )
    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Course, COURSE_ID).vertex_enabled is False


def test_admin_set_course_vertex_requires_login(client, course):
    response = client.put(
        "/admin_set_course_vertex", json={"course_id": COURSE_ID, "enabled": True}
    )
    assert response.status_code == 401


def test_instructor_cannot_enable_vertex(client, course, login_as):
    login_as(INSTRUCTOR_ID)

    response = client.put(
        "/admin_set_course_vertex", json={"course_id": COURSE_ID, "enabled": True}
    )

    assert response.status_code == 403
    assert db.session.get(Course, COURSE_ID).vertex_enabled is False


@pytest.mark.parametrize("enabled", [None, "true", 1])
def test_admin_set_course_vertex_requires_boolean(client, course, login_as, enabled):
    login_as(ADMIN_ID)

    response = client.put(
        "/admin_set_course_vertex", json={"course_id": COURSE_ID, "enabled": enabled}
    )

    assert response.status_code == 400


def test_admin_set_course_vertex_unknown_course(client, course, login_as):
    login_as(ADMIN_ID)

    response = client.put(
        "/admin_set_course_vertex",
        json={"course_id": "deadbeef-0000-4000-8000-00000000abcd", "enabled": True},
    )

    assert response.status_code == 404


def test_all_courses_listing_includes_vertex_flag(client, course, login_as):
    _enable_vertex()
    login_as(ADMIN_ID)

    response = client.get("/get_all_courses")

    assert response.status_code == 200
    assert response.json[0]["vertex_enabled"] is True


# -- Course-level settings and Vertex test endpoints ----------------------------

def test_course_info_reports_vertex_disabled(client, course, login_as):
    login_as(INSTRUCTOR_ID)

    response = client.get("/get_course_info", query_string={"course_id": COURSE_ID})

    body = response.json[0]
    assert body["vertex_enabled"] is False
    assert body["has_vertex_server_config"] is True
    assert body["has_gemini_vertex_config"] is False


def test_course_info_reports_vertex_enabled(client, course, login_as):
    _enable_vertex()
    login_as(INSTRUCTOR_ID)

    response = client.get("/get_course_info", query_string={"course_id": COURSE_ID})

    assert response.json[0]["has_gemini_vertex_config"] is True


def test_course_default_vertex_rejected_when_not_enabled(client, course, login_as):
    login_as(INSTRUCTOR_ID)

    response = client.put("/update_ai_settings", json={
        "course_id": COURSE_ID,
        "provider": "gemini_vertex",
        "model_name": "gemini-2.5-flash",
    })

    assert response.status_code == 403
    assert "not enabled" in response.json["message"]
    assert db.session.get(Course, COURSE_ID).default_ai_provider != "gemini_vertex"


def test_course_default_vertex_allowed_when_enabled(client, course, login_as):
    _enable_vertex()
    login_as(INSTRUCTOR_ID)

    response = client.put("/update_ai_settings", json={
        "course_id": COURSE_ID,
        "provider": "gemini_vertex",
        "model_name": "gemini-2.5-flash",
    })

    assert response.status_code == 200


@pytest.mark.parametrize("endpoint", ["/fetch_ai_models", "/test_ai_api_key", "/test_ai_model"])
def test_vertex_endpoints_rejected_when_not_enabled(client, course, login_as, mocker, endpoint):
    mock_client = mocker.patch("routes.course.create_gemini_client")
    login_as(INSTRUCTOR_ID)

    response = client.post(endpoint, json={
        "course_id": COURSE_ID,
        "provider": "gemini_vertex",
        "model": "gemini-2.5-flash",
    })

    assert response.status_code == 403
    assert "not enabled" in response.json["message"]
    mock_client.assert_not_called()


def test_fetch_vertex_models_when_enabled(client, course, login_as):
    _enable_vertex()
    login_as(TA_ID)

    response = client.post("/fetch_ai_models", json={
        "course_id": COURSE_ID,
        "provider": "gemini_vertex",
    })

    assert response.status_code == 200
    assert "gemini-2.5-flash" in response.json["models"]


# -- Assignment overrides ----------------------------------------------------------

def test_instructor_cannot_set_vertex_override_when_not_enabled(client, course, login_as):
    login_as(INSTRUCTOR_ID)

    response = _put_ai_settings(client, _vertex_override())

    assert response.status_code == 403
    assert "not enabled" in response.json["message"]
    assert db.session.get(Assignment, ASSIGNMENT_ID).ai_feedback_provider is None


def test_instructor_can_set_vertex_override_when_enabled(client, course, login_as):
    _enable_vertex()
    login_as(INSTRUCTOR_ID)

    response = _put_ai_settings(client, _vertex_override())

    assert response.status_code == 200
    assert db.session.get(Assignment, ASSIGNMENT_ID).ai_feedback_provider == "gemini_vertex"


def test_ta_cannot_set_vertex_override(client, course, login_as):
    _enable_vertex()
    login_as(TA_ID)

    response = _put_ai_settings(client, _vertex_override())

    assert response.status_code == 403
    assert "Only instructors" in response.json["message"]
    assert db.session.get(Assignment, ASSIGNMENT_ID).ai_feedback_provider is None


def _instructor_sets_vertex(client, login_as):
    _enable_vertex()
    login_as(INSTRUCTOR_ID)
    assert _put_ai_settings(client, _vertex_override()).status_code == 200


def test_ta_can_resave_unchanged_vertex_override(client, course, login_as):
    _instructor_sets_vertex(client, login_as)
    login_as(TA_ID)

    response = _put_ai_settings(client, _vertex_override(ai_feedback_style="direct"))

    assert response.status_code == 200
    assignment = db.session.get(Assignment, ASSIGNMENT_ID)
    assert assignment.ai_feedback_style == "direct"
    assert assignment.ai_feedback_provider == "gemini_vertex"


@pytest.mark.parametrize("change", [
    {"ai_feedback_model": "gemini-2.5-pro"},
    {"ai_feedback_vertex_location": "us-central1"},
])
def test_ta_cannot_change_vertex_model_or_location(client, course, login_as, change):
    _instructor_sets_vertex(client, login_as)
    login_as(TA_ID)

    response = _put_ai_settings(client, _vertex_override(**change))

    assert response.status_code == 403


def test_ta_can_switch_vertex_assignment_to_other_provider(client, course, login_as):
    _instructor_sets_vertex(client, login_as)
    login_as(TA_ID)

    response = _put_ai_settings(client, {
        "use_course_ai_default": False,
        "ai_feedback_provider": "openai",
        "ai_feedback_model": "gpt-4o-mini",
    })

    assert response.status_code == 200


def test_ta_can_set_non_vertex_override(client, course, login_as):
    login_as(TA_ID)

    response = _put_ai_settings(client, {
        "use_course_ai_default": False,
        "ai_feedback_provider": "openai",
        "ai_feedback_model": "gpt-4o-mini",
    })

    assert response.status_code == 200


def test_ta_cannot_set_vertex_through_update_assignment(client, course, login_as):
    _enable_vertex()
    login_as(TA_ID)

    response = client.put("/update_assignment", json={
        "assignment_id": ASSIGNMENT_ID,
        "name": "HW1",
        "course_id": COURSE_ID,
        **_vertex_override(),
    })

    assert response.status_code == 403
    assert db.session.get(Assignment, ASSIGNMENT_ID).ai_feedback_provider is None


def test_ta_cannot_create_assignment_with_vertex(client, course, login_as):
    _enable_vertex()
    login_as(TA_ID)

    response = client.post("/create_assignment", json={
        "name": "HW2",
        "course_id": COURSE_ID,
        **_vertex_override(),
    })

    assert response.status_code == 403
    assert db.session.query(Assignment).filter_by(name="HW2").first() is None


def test_instructor_can_create_assignment_with_vertex(client, course, login_as):
    _enable_vertex()
    login_as(INSTRUCTOR_ID)

    response = client.post("/create_assignment", json={
        "name": "HW2",
        "course_id": COURSE_ID,
        **_vertex_override(),
    })

    assert response.status_code == 200
    created = db.session.query(Assignment).filter_by(name="HW2").first()
    assert created.ai_feedback_provider == "gemini_vertex"


# -- Instructors cannot grant themselves Vertex through course routes ----------

def test_instructor_cannot_create_course_with_vertex_enabled(client, course, login_as):
    login_as(INSTRUCTOR_ID)

    response = client.post("/create_course", json={
        "name": "CS 102",
        "instructor_id": INSTRUCTOR_ID,
        "semester": "Fall",
        "year": "2026",
        "entryCode": "ENTRY2",
        "vertex_enabled": True,
    })

    assert response.status_code == 201
    created = db.session.query(Course).filter_by(entryCode="ENTRY2").first()
    assert created.vertex_enabled is False


def test_instructor_cannot_enable_vertex_through_update_course(client, course, login_as):
    login_as(INSTRUCTOR_ID)

    response = client.put("/update_course", json={
        "course_id": COURSE_ID,
        "description": "",
        "name": "CS 101",
        "semester": "Fall",
        "year": "2026",
        "entryCode": "ENTRY1",
        "allowEntryCode": True,
        "vertex_enabled": True,
    })

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Course, COURSE_ID).vertex_enabled is False
