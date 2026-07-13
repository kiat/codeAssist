"""
Integration tests for cascade delete behavior and RESTRICT constraint on
instructor_id, as required by PR #312 review (Dario, July 8).

SQLite does not enforce foreign keys by default — these tests enable
enforcement via PRAGMA foreign_keys=ON and exercise real DB-level cascade
and restriction behavior.
"""
import uuid
import pytest
from api import create_app
from api.models import db, User, Course, Enrollment, Assignment, Submission


@pytest.fixture
def app():
    """Create an app with SQLite FK enforcement enabled."""
    app = create_app(config_class="config.TestConfig")

    with app.app_context():
        db.create_all()
        # Enable foreign key enforcement in SQLite
        db.session.execute(db.text("PRAGMA foreign_keys=ON"))
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_session(client, app):
    """Create an admin user and log them in for admin-only endpoints."""
    admin_id = str(uuid.uuid4())
    with app.app_context():
        admin = User(
            id=admin_id,
            name="Admin",
            email_address="admin@test.com",
            password="hashedpw",
            sis_user_id="ADMIN-EID",
            role="admin",
            coding_insights="No history.",
        )
        db.session.add(admin)
        db.session.commit()
    with client.session_transaction() as sess:
        sess["user_id"] = admin_id
    return admin_id


def _create_user(client, name, email, eid, role="student"):
    """Helper to create a user via the API and return the user_id."""
    resp = client.post("/create_user", json={
        "name": name,
        "email_address": email,
        "password": "password123",
        "eid": eid,
        "role": role,
    })
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["id"]


def _create_course(client, instructor_id, name="Test Course", entry_code=None):
    """Helper to create a course and return the course_id."""
    if entry_code is None:
        entry_code = f"EC-{uuid.uuid4().hex[:6]}"
    resp = client.post("/create_course", json={
        "name": name,
        "instructor_id": instructor_id,
        "semester": "Fall",
        "year": "2026",
        "entryCode": entry_code,
    })
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["id"]


def _enroll_student(client, student_id, course_id):
    """Helper to enroll a student in a course."""
    resp = client.post("/create_enrollment", json={
        "student_id": student_id,
        "course_id": course_id,
        "role": "student",
    })
    assert resp.status_code == 201, resp.get_json()


def _create_assignment(client, course_id, name="HW1"):
    """Helper to create an assignment via the API."""
    resp = client.post("/create_assignment", json={
        "name": name,
        "course_id": course_id,
    })
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()["id"]


def _create_submission_via_api(client, assignment_id, student_id):
    """Create a submission directly in the DB (bypasses Docker autograder)."""
    sub = Submission(
        id=str(uuid.uuid4()),
        file_name="solution.py",
        submission_number=1,
        student_id=student_id,
        assignment_id=assignment_id,
        student_code_file=b"print('hello')",
        results=None,
        score=None,
        execution_time=0.0,
        active=True,
        completed=True,
        ai_feedback=None,
    )
    db.session.add(sub)
    db.session.commit()
    return sub.id


# ----------------------------------------------------------------
# Tests
# ----------------------------------------------------------------

def test_delete_student_cascades_enrollment_and_submissions(client, admin_session):
    """Deleting a student should cascade-delete their enrollments and submissions."""
    student_id = _create_user(client, "Alice", "alice@example.com", "EID-ALICE")
    instructor_id = _create_user(client, "Prof", "prof@example.com", "EID-PROF", "instructor")
    course_id = _create_course(client, instructor_id)

    _enroll_student(client, student_id, course_id)
    assignment_id = _create_assignment(client, course_id)
    submission_id = _create_submission_via_api(client, assignment_id, student_id)

    # Verify rows exist before deletion
    assert db.session.query(Enrollment).filter_by(
        student_id=student_id, course_id=course_id
    ).first() is not None
    assert db.session.query(Submission).filter_by(id=submission_id).first() is not None

    # Delete the student
    resp = client.delete(f"/delete_user?id={student_id}")
    assert resp.status_code == 200

    # Verify cascaded rows are gone
    assert db.session.query(User).filter_by(id=student_id).first() is None
    assert db.session.query(Enrollment).filter_by(
        student_id=student_id, course_id=course_id
    ).first() is None
    assert db.session.query(Submission).filter_by(id=submission_id).first() is None

    # Course and instructor should still exist
    assert db.session.query(Course).filter_by(id=course_id).first() is not None
    assert db.session.query(User).filter_by(id=instructor_id).first() is not None


def test_delete_instructor_with_active_courses_is_rejected(client, admin_session):
    """Deleting an instructor who owns courses must be blocked by RESTRICT."""
    instructor_id = _create_user(client, "Prof", "prof@example.com", "EID-PROF", "instructor")
    course_id = _create_course(client, instructor_id)

    # Verify the course exists
    assert db.session.query(Course).filter_by(id=course_id).first() is not None

    # Attempt to delete the instructor — should fail (RESTRICT)
    resp = client.delete(f"/delete_user?id={instructor_id}")

    # The API should return 409 (ConflictError) — RESTRICT prevents deletion
    assert resp.status_code == 409, (
        f"Expected 409 when deleting instructor with courses, got {resp.status_code}"
    )

    # Instructor should still exist
    assert db.session.query(User).filter_by(id=instructor_id).first() is not None
    assert db.session.query(Course).filter_by(id=course_id).first() is not None


def test_delete_student_does_not_affect_other_students(client, admin_session):
    """Deleting one student should not affect other students' data."""
    student_a = _create_user(client, "Alice", "alice@example.com", "EID-A")
    student_b = _create_user(client, "Bob", "bob@example.com", "EID-B")
    instructor_id = _create_user(client, "Prof", "prof@example.com", "EID-PROF", "instructor")
    course_id = _create_course(client, instructor_id)

    _enroll_student(client, student_a, course_id)
    _enroll_student(client, student_b, course_id)

    assignment_id = _create_assignment(client, course_id)
    sub_a = _create_submission_via_api(client, assignment_id, student_a)
    sub_b = _create_submission_via_api(client, assignment_id, student_b)

    # Delete student A
    resp = client.delete(f"/delete_user?id={student_a}")
    assert resp.status_code == 200

    # Student A's data should be gone
    assert db.session.query(Enrollment).filter_by(student_id=student_a).first() is None
    assert db.session.query(Submission).filter_by(id=sub_a).first() is None

    # Student B's data should be untouched
    assert db.session.query(User).filter_by(id=student_b).first() is not None
    assert db.session.query(Enrollment).filter_by(
        student_id=student_b, course_id=course_id
    ).first() is not None
    assert db.session.query(Submission).filter_by(id=sub_b).first() is not None
