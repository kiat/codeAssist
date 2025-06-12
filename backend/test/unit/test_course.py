import pytest
from api import create_app
from util.errors import BadRequestError, ConflictError, NotFoundError, InternalProcessingError
from routes.course import allowed_file, create_enrollment_bulk

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        from routes.course import db  
        db.create_all()  
        yield app
        db.session.remove()
        db.drop_all() 

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def mock_course_query(mocker):
    """Mock the database query for courses."""
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_schema = mocker.patch("routes.course.CourseSchema")
    return mock_query, mock_schema


def test_create_course_success(client, mocker, mock_course_query):
    mock_query, mock_schema = mock_course_query

    mock_query.return_value.filter_by.return_value.first.return_value = None
    mock_add = mocker.patch("routes.course.db.session.add")
    mock_commit = mocker.patch("routes.course.db.session.commit")
    
    mock_schema.return_value.dump.return_value = {
        "id": "course-id",
        "name": "CS101"
    }

    payload = {
        "name": "CS101",
        "instructor_id": "user-123",
        "semester": "Fall",
        "year": "2025",
        "entryCode": "ABCD1234"
    }

    response = client.post("/create_course", json=payload)

    assert response.status_code == 201
    assert response.json["name"] == "CS101"
    mock_commit.assert_called_once()
    assert mock_add.call_count == 2


def test_create_course_duplicate_entry_code(client, mock_course_query):
    mock_query, _ = mock_course_query
    mock_query.return_value.filter_by.return_value.first.return_value = True

    payload = {
        "name": "CS101",
        "instructor_id": "user-123",
        "semester": "Fall",
        "year": "2025",
        "entryCode": "DUPLICATE"
    }

    response = client.post("/create_course", json=payload)

    assert response.status_code == 409
    assert response.json["message"] == "Course with the provided entry code already exists"


def test_create_course_missing_fields(client):
    payload = {
        "name": "CS101",
        "semester": "Fall",
        "year": "2025"
        # Missing instructor_id and entryCode
    }

    response = client.post("/create_course", json=payload)

    assert response.status_code == 400
    assert response.json["message"] == "Missing required fields"


def test_enroll_course_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_commit = mocker.patch("routes.course.db.session.commit")
    mock_add = mocker.patch("routes.course.db.session.add")

    mock_course = mocker.Mock()
    mock_course.id = "course-123"
    mock_course.allowEntryCode = True

    # First query returns course
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_course,  # for course lookup
        None          # no existing enrollment
    ]

    payload = {
        "user_id": "student-456",
        "entryCode": "JOIN123"
    }

    response = client.post("/enroll_course", json=payload)

    assert response.status_code == 201
    mock_add.assert_called_once()
    mock_commit.assert_called_once()


def test_enroll_course_already_enrolled(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_course = mocker.Mock()
    mock_course.id = "course-123"
    mock_course.allowEntryCode = True

    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mock_course,   # course found
        True           # already enrolled
    ]

    payload = {
        "user_id": "student-456",
        "entryCode": "JOIN123"
    }

    response = client.post("/enroll_course", json=payload)

    assert response.status_code == 409
    assert response.json["message"] == "User is already enrolled in this course"


def test_enroll_course_invalid_code(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")

    # course does not exist
    mock_query.return_value.filter_by.return_value.first.return_value = None

    payload = {
        "user_id": "student-456",
        "entryCode": "INVALID123"
    }

    response = client.post("/enroll_course", json=payload)

    assert response.status_code == 404
    assert response.json["message"] == "Course with the provided entry code does not exist"

def test_update_course_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_commit = mocker.patch("routes.course.db.session.commit")

    # Mock the query object and its methods
    mock_query_instance = mocker.Mock()
    mock_query.return_value.filter_by.return_value = mock_query_instance
    mock_query_instance.update = mocker.Mock()

    mock_query.return_value.filter_by.return_value.first.return_value = None  # No duplicate entryCode

    payload = {
        "course_id": "course-123",
        "description": "Updated description",
        "name": "Updated Course Name",
        "semester": "Spring",
        "year": "2025",
        "entryCode": "NEWCODE123",
        "allowEntryCode": True
    }

    response = client.put("/update_course", json=payload)

    assert response.status_code == 200
    assert response.json["message"] == "Course updated successfully"
    mock_query_instance.update.assert_called_once()
    mock_commit.assert_called_once()


def test_update_course_duplicate_entry_code(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = mocker.Mock(id="different-course-id")  # Duplicate entryCode

    payload = {
        "course_id": "course-123",
        "description": "Updated description",
        "name": "Updated Course Name",
        "semester": "Spring",
        "year": "2025",
        "entryCode": "DUPLICATECODE",
        "allowEntryCode": True
    }

    response = client.put("/update_course", json=payload)

    assert response.status_code == 409
    assert response.json["message"] == "Course with the provided entry code already exists"

def test_delete_course_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_delete = mocker.patch("routes.course.db.session.delete")
    mock_commit = mocker.patch("routes.course.db.session.commit")

    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mocker.Mock(),  # Course exists
        None            # No assignments
    ]

    response = client.delete("/delete_course", query_string={"course_id": "course-123"})

    assert response.status_code == 200
    assert response.json["message"] == "Course deleted successfully"
    mock_delete.assert_called()
    mock_commit.assert_called()


def test_delete_course_with_assignments(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mocker.Mock(),  # Course exists
        mocker.Mock()   # Assignments exist
    ]

    response = client.delete("/delete_course", query_string={"course_id": "course-123"})

    assert response.status_code == 409
    assert response.json["message"] == "Cannot delete course with assignments"

def test_delete_all_assignments_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_commit = mocker.patch("routes.course.db.session.commit")

    mock_query.return_value.filter_by.return_value.all.return_value = [mocker.Mock(id="assignment-1")]

    response = client.delete("/delete_all_assignments", query_string={"course_id": "course-123"})

    assert response.status_code == 200
    assert response.json == "Assignments deleted successfully"
    mock_commit.assert_called()


def test_delete_all_assignments_not_found(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query.return_value.filter_by.return_value.all.return_value = []

    response = client.delete("/delete_all_assignments", query_string={"course_id": "course-123"})

    assert response.status_code == 404
    assert response.json["message"] == "No assignments found for this course"

def test_create_enrollment_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_add = mocker.patch("routes.course.db.session.add")
    mock_commit = mocker.patch("routes.course.db.session.commit")

    mock_query.return_value.filter_by.return_value.first.return_value = None  # No existing enrollment

    payload = {
        "student_id": "student-123",
        "course_id": "course-123"
    }

    response = client.post("/create_enrollment", json=payload)

    assert response.status_code == 201
    assert "student_id" in response.json
    mock_add.assert_called_once()
    mock_commit.assert_called_once()

def test_create_enrollment_already_enrolled(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = mocker.Mock()  # Already enrolled

    payload = {
        "student_id": "student-123",
        "course_id": "course-123"
    }

    response = client.post("/create_enrollment", json=payload)

    assert response.status_code == 409
    assert response.json["message"] == "User is already enrolled in this course"

def test_update_role_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_commit = mocker.patch("routes.course.db.session.commit")

    enrollment = mocker.Mock()
    mock_query.return_value.filter_by.return_value.first.return_value = enrollment

    payload = {
        "student_id": "student-123",
        "course_id": "course-123",
        "new_role": "TA"
    }

    response = client.post("/update_role", json=payload)

    assert response.status_code == 200
    assert response.json["role"] == "TA"
    assert enrollment.role == "TA"
    mock_commit.assert_called_once()

def test_update_role_not_found(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None  # Enrollment not found

    payload = {
        "student_id": "student-123",
        "course_id": "course-123",
        "new_role": "TA"
    }

    response = client.post("/update_role", json=payload)

    assert response.status_code == 404
    assert response.json["message"] == "Enrollment not found"

import io

def test_create_enrollment_csv_success(client, mocker):
    # create a file like object to simulate the uploaded file
    file_content = "student-1\nstudent-2"
    mock_file = (io.BytesIO(file_content.encode()), "students.csv")

    # Mock dependencies
    mocker.patch("routes.course.allowed_file", return_value=True)
    mocker.patch("routes.course.os.path.exists", return_value=False)
    mocker.patch("routes.course.os.makedirs")
    mocker.patch("routes.course.os.remove")
    mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data=file_content))
    mock_create_bulk = mocker.patch("routes.course.create_enrollment_bulk", return_value={"failed_enrollments": []})

    data = {
        "file": mock_file,
        "course_id": "course-123"
    }

    response = client.post("/create_enrollment_csv", data=data, content_type="multipart/form-data")

    assert response.status_code == 200
    assert response.json["failed_enrollments"] == []
    mock_open.assert_any_call(mocker.ANY, newline="")  
    mock_create_bulk.assert_called_once_with({"course_id": "course-123", "student_ids": ["student-1", "student-2"]})


def test_create_enrollment_csv_missing_file(client, mocker):
    response = client.post("/create_enrollment_csv", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert response.json["message"] == "Missing file part"

def test_get_user_enrollments_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query.return_value.filter_by.return_value = [mocker.Mock(course_id="course-123")]
    mock_query.return_value.filter.return_value = [mocker.Mock(id="course-123", name="CS101")]
    mock_schema = mocker.patch("routes.course.CourseSchema")
    mock_schema.return_value.dump.return_value = [{"id": "course-123", "name": "CS101"}]

    response = client.get("/get_user_enrollments", query_string={"user_id": "user-123"})

    assert response.status_code == 200
    assert response.json == [{"id": "course-123", "name": "CS101"}]

def test_get_user_enrollments_missing_user_id(client):
    response = client.get("/get_user_enrollments")
    assert response.status_code == 400
    assert response.json["message"] == "Missing user_id argument"

def test_get_course_enrollment_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query.return_value.filter_by.return_value = [mocker.Mock(student_id="student-123")]
    mock_query.return_value.filter.return_value = [mocker.Mock(name="John Doe", email_address="john@example.com", id="student-123", role="student")]
    mock_schema = mocker.patch("routes.course.UserSchema")
    mock_schema.return_value.dump.return_value = [{"name": "John Doe", "email_address": "john@example.com", "id": "student-123", "role": "student"}]

    response = client.get("/get_course_enrollment", query_string={"course_id": "course-123"})

    assert response.status_code == 200
    assert response.json == [{"name": "John Doe", "email_address": "john@example.com", "id": "student-123", "role": "student"}]

def test_get_course_enrollment_missing_course_id(client):
    response = client.get("/get_course_enrollment")
    assert response.status_code == 400
    assert response.json["message"] == "Missing course_id argument"

def test_get_course_assignments_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query.return_value.filter_by.return_value.all.return_value = [mocker.Mock(id="assignment-1", name="Assignment 1")]
    mock_schema = mocker.patch("routes.course.AssignmentSchema")
    mock_schema.return_value.dump.return_value = [{"id": "assignment-1", "name": "Assignment 1"}]

    response = client.get("/get_course_assignments", query_string={"course_id": "course-123"})

    assert response.status_code == 200
    assert response.json == [{"id": "assignment-1", "name": "Assignment 1"}]

def test_get_course_assignments_missing_course_id(client):
    response = client.get("/get_course_assignments")
    assert response.status_code == 400
    assert response.json["message"] == "Missing course_id argument"

def test_get_course_info_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query.return_value.filter_by.return_value = [mocker.Mock(id="course-123", name="CS101")]
    mock_schema = mocker.patch("routes.course.CourseSchema")
    mock_schema.return_value.dump.return_value = [{"id": "course-123", "name": "CS101"}]

    response = client.get("/get_course_info", query_string={"course_id": "course-123"})

    assert response.status_code == 200
    assert response.json == [{"id": "course-123", "name": "CS101"}]


def test_get_course_info_missing_course_id(client):
    response = client.get("/get_course_info")
    assert response.status_code == 400
    assert response.json["message"] == "Missing course_id argument"

def test_allowed_file_true():
    assert allowed_file("students.csv") == True

def test_allowed_file_false():
    assert allowed_file("students.txt") == False

def test_create_enrollment_bulk_success(mocker):
    mock_add = mocker.patch("routes.course.db.session.add")
    mock_commit = mocker.patch("routes.course.db.session.commit")

    data = {
        "course_id": "course-1",
        "student_ids": ["a", "b", "b"],  # should deduplicate
        "role": "student"
    }

    response = create_enrollment_bulk(data)

    assert response == {"failed_enrollments": []}
    assert mock_add.call_count == 2  # "a" and "b" only once
    assert mock_commit.call_count == 2

def test_create_enrollment_bulk_with_failures(mocker):
    def raise_error(*args, **kwargs):
        raise Exception()

    mocker.patch("routes.course.db.session.add", side_effect=raise_error)
    mocker.patch("routes.course.db.session.commit", side_effect=raise_error)

    data = {
        "course_id": "course-1",
        "student_ids": ["a", "b"]
    }

    result = create_enrollment_bulk(data)
    assert set(result["failed_enrollments"]) == {"a", "b"}  # Compare as sets to ignore order

def test_create_course_get_not_allowed(client):
    response = client.get("/create_course")
    assert response.status_code == 415

def test_create_course_db_error(client, mocker):
    mocker.patch("routes.course.db.session.add")
    mocker.patch("routes.course.db.session.commit", side_effect=Exception("fail"))
    mocker.patch("routes.course.db.session.rollback")

    payload = {
        "name": "Test",
        "instructor_id": "inst-1",
        "semester": "Fall",
        "year": "2025",
        "entryCode": "ERR123"
    }

    response = client.post("/create_course", json=payload)
    assert response.status_code == 500
    assert response.json["message"] == "Failed to create course"

def test_update_course_db_error(client, mocker):
    mocker.patch("routes.course.db.session.query")
    mocker.patch("routes.course.db.session.commit", side_effect=Exception("fail"))
    mocker.patch("routes.course.db.session.rollback")

    payload = {
        "course_id": "course-123",
        "description": "Updated descrip/tetion",
        "name": "Updated Course Name",
        "semester": "Spring",
        "year": "2025",
        "entryCode": "NEWCODE123",
        "allowEntryCode": True
    }

    response = client.put("/update_course", json=payload)
    assert response.status_code == 409
    assert response.json["message"] == "Course with the provided entry code already exists"

def test_delete_course_db_error(client, mocker):
    mocker.patch("routes.course.db.session.query")
    mocker.patch("routes.course.db.session.commit", side_effect=Exception("fail"))
    mocker.patch("routes.course.db.session.rollback")

    response = client.delete("/delete_course", query_string={"course_id": "course-123"})
    assert response.status_code == 409
    assert response.json["message"] == "Cannot delete course with assignments"

def test_enroll_course_db_error(client, mocker):
    mocker.patch("routes.course.db.session.query")
    mocker.patch("routes.course.db.session.add")
    mocker.patch("routes.course.db.session.commit", side_effect=Exception("fail"))
    mocker.patch("routes.course.db.session.rollback")

    payload = {
        "user_id": "student-123",
        "entryCode": "VALID123"
    }

    response = client.post("/enroll_course", json=payload)
    assert response.status_code == 409
    assert response.json["message"] == "User is already enrolled in this course"