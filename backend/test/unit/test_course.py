import pytest
from api import create_app
from api.models import Course, Enrollment

@pytest.fixture
def app():
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

# -------------------------------
# /create_course
# -------------------------------

def test_create_course_success(client, mocker):
    mock_add = mocker.patch("routes.course.db.session.add")
    mock_commit = mocker.patch("routes.course.db.session.commit")
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_schema = mocker.patch("routes.course.CourseSchema")

    mock_query.return_value.filter_by.return_value.first.return_value = None
    mock_schema.return_value.dump.return_value = {"id": "fake-id", "name": "Test Course"}

    payload = {
        "name": "Test Course",
        "instructor_id": "instructor1",
        "semester": "Fall",
        "year": "2024",
        "entryCode": "ABC123"
    }

    response = client.post("/create_course", json=payload)

    assert response.status_code == 201
    assert response.json["name"] == "Test Course"
    assert mock_add.call_count == 2
    mock_commit.assert_called_once()

def test_create_course_duplicate_entry_code(client, mocker):
    mock_add = mocker.patch("routes.course.db.session.add")
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = True

    payload = {
        "name": "Test Course",
        "instructor_id": "instructor1",
        "semester": "Fall",
        "year": "2024",
        "entryCode": "DUPLICATE"
    }

    response = client.post("/create_course", json=payload)
    assert response.status_code == 409
    mock_add.assert_not_called()

def test_create_course_missing_fields(client):
    response = client.post("/create_course", json={"name": "Test Course"})
    assert response.status_code == 400

# -------------------------------
# /enroll_course
# -------------------------------

def test_enroll_course_success(client, mocker):
    mock_add = mocker.patch("routes.course.db.session.add")
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_commit = mocker.patch("routes.course.db.session.commit")
    mock_schema = mocker.patch("routes.course.EnrollmentSchema")

    course_mock = mocker.Mock()
    course_mock.id = "course-id"
    course_mock.allowEntryCode = True

    # course query
    course_filter = mocker.Mock()
    course_filter.first.return_value = course_mock

    # enrollment check
    enrollment_filter = mocker.Mock()
    enrollment_filter.first.return_value = None

    def side_effect(model):
        if model == Course:
            return mocker.Mock(filter_by=mocker.Mock(return_value=course_filter))
        elif model == Enrollment:
            return mocker.Mock(filter_by=mocker.Mock(return_value=enrollment_filter))
        return mocker.Mock()

    mock_query.side_effect = side_effect
    mock_schema.return_value.dump.return_value = {"course_id": "course-id"}

    payload = {"entryCode": "ABC123", "user_id": "user-id"}

    response = client.post("/enroll_course", json=payload)

    assert response.status_code == 201
    assert response.json["course_id"] == "course-id"

    mock_add.assert_called_once()
    mock_commit.assert_called_once()

def test_enroll_course_missing_fields(client):
    response = client.post("/enroll_course", json={"entryCode": "ABC123"})
    assert response.status_code == 400

# -------------------------------
# /update_course
# -------------------------------

def test_update_course_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_commit = mocker.patch("routes.course.db.session.commit")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    payload = {
        "course_id": "C1",
        "name": "Updated",
        "description": "New desc",
        "semester": "Fall",
        "year": "2024",
        "entryCode": "E123",
        "allowEntryCode": True
    }

    response = client.put("/update_course", json=payload)

    assert response.status_code == 200
    assert response.json["message"] == "Course updated successfully"
    mock_commit.assert_called_once()

# -------------------------------
# /delete_course
# -------------------------------

def test_delete_course_success(client, mocker):
    mock_db = mocker.patch("routes.course.db")

    # Mock the course object returned by the first query
    mock_course = mocker.Mock()
    mock_course.id = "C1"
    mock_course.name = "Sample"

    # Patch query and configure sequential return values
    mock_query = mocker.patch("routes.course.db.session.query")

    mock_course_query = mocker.Mock()
    mock_course_filter = mocker.Mock()
    mock_course_filter.first.return_value = mock_course
    mock_course_query.filter_by.return_value = mock_course_filter

    mock_assignment_query = mocker.Mock()
    mock_assignment_filter = mocker.Mock()
    mock_assignment_filter.first.return_value = None
    mock_assignment_query.filter_by.return_value = mock_assignment_filter

    mock_enrollment_query = mocker.Mock()
    mock_enrollment_filter = mocker.Mock()
    mock_enrollment_filter.all.return_value = [mocker.Mock()]
    mock_enrollment_query.filter_by.return_value = mock_enrollment_filter

    mock_query.side_effect = [mock_course_query, mock_assignment_query, mock_enrollment_query]

    response = client.delete("/delete_course?course_id=C1")

    assert response.status_code == 200
    assert b"Course deleted successfully" in response.data

    # Assertions for key method calls
    mock_course_query.filter_by.assert_called_once_with(id="C1")
    mock_assignment_query.filter_by.assert_called_once_with(course_id="C1")
    mock_enrollment_query.filter_by.assert_called_once_with(course_id="C1")

    assert mock_db.session.delete.call_count == 2
    assert mock_db.session.commit.call_count == 2  # one for enrollments, one for course delete


def test_delete_course_missing_id(client):
    response = client.delete("/delete_course")
    assert response.status_code == 400

# -------------------------------
# /delete_all_assignments
# -------------------------------

def test_delete_all_assignments_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_commit = mocker.patch("routes.course.db.session.commit")
    mock_query.return_value.filter_by.return_value.all.return_value = [mocker.Mock(id="A1")]

    response = client.delete("/delete_all_assignments?course_id=C1")
    assert response.status_code == 200

def test_delete_all_assignments_missing_id(client):
    response = client.delete("/delete_all_assignments")
    assert response.status_code == 400

# -------------------------------
# /create_enrollment
# -------------------------------

def test_create_enrollment_success(client, mocker):
    mock_add = mocker.patch("routes.course.db.session.add")
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_commit = mocker.patch("routes.course.db.session.commit")
    mock_query.return_value.filter_by.return_value.first.return_value = None
    mock_schema = mocker.patch("routes.course.EnrollmentSchema")
    mock_schema.return_value.dump.return_value = {"course_id": "C1"}

    payload = {"student_id": "S1", "course_id": "C1"}

    response = client.post("/create_enrollment", json=payload)
    assert response.status_code == 201

    mock_add.assert_called_once()
    mock_commit.assert_called_once()

# -------------------------------
# /update_role
# -------------------------------

def test_update_role_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_commit = mocker.patch("routes.course.db.session.commit")
    mock_schema = mocker.patch("routes.course.EnrollmentSchema")

    mock_enrollment = mocker.Mock()
    mock_query.return_value.filter_by.return_value.first.return_value = mock_enrollment
    mock_schema.return_value.dump.return_value = {"new_role": "TA"}

    payload = {"student_id": "S1", "course_id": "C1", "new_role": "TA"}

    response = client.post("/update_role", json=payload)
    assert response.status_code == 200

    mock_commit.assert_called_once()

# -------------------------------
# /create_enrollment_csv
# -------------------------------

def test_create_enrollment_csv_missing_file(client):
    response = client.post("/create_enrollment_csv", data={})
    assert response.status_code == 400

# -------------------------------
# /get_user_enrollments
# -------------------------------

def test_get_user_enrollments_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_schema = mocker.patch("routes.course.CourseSchema")
    mock_query.return_value.filter_by.return_value = [mocker.Mock(course_id="C1")]
    mock_schema.return_value.dump.return_value = [{"id": "C1"}]

    response = client.get("/get_user_enrollments?user_id=U1")
    assert response.status_code == 200
    assert response.json == [{"id": "C1"}]

# -------------------------------
# /get_course_enrollment
# -------------------------------

def test_get_course_enrollment_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_enrollment_schema = mocker.patch("routes.course.EnrollmentSchema")
    mock_user_schema = mocker.patch("routes.course.UserSchema")

    mock_enrollment_schema.return_value.dump.return_value = [{"student_id": "U1"}]
    mock_user_schema.return_value.dump.return_value = [{"name": "Test User"}]

    response = client.get("/get_course_enrollment?course_id=C1")
    assert response.status_code == 200

# -------------------------------
# /get_course_assignments
# -------------------------------

def test_get_course_assignments_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_schema = mocker.patch("routes.course.AssignmentSchema")

    mock_query.return_value.filter_by.return_value.all.return_value = ["A1"]
    mock_schema.return_value.dump.return_value = [{"id": "A1"}]

    response = client.get("/get_course_assignments?course_id=C1")
    assert response.status_code == 200
    assert response.json == [{"id": "A1"}]

# -------------------------------
# /get_course_info
# -------------------------------

def test_get_course_info_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_schema = mocker.patch("routes.course.CourseSchema")
    mock_schema.return_value.dump.return_value = [{"id": "C1"}]

    response = client.get("/get_course_info?course_id=C1")
    assert response.status_code == 200
    assert response.json == [{"id": "C1"}]
