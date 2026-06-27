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
    mocker.patch("routes.course.get_user_course_role", return_value="instructor")

    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mocker.Mock(),  # Course exists
        None            # No assignments
    ]

    response = client.delete("/delete_course", query_string={"course_id": "course-123", "requester_id": "req-123"})

    assert response.status_code == 200
    assert response.json["message"] == "Course deleted successfully"
    mock_delete.assert_called()
    mock_commit.assert_called()


def test_delete_course_with_assignments(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mocker.patch("routes.course.get_user_course_role", return_value="instructor")
    mock_query.return_value.filter_by.return_value.first.side_effect = [
        mocker.Mock(),  # Course exists
        mocker.Mock()   # Assignments exist
    ]

    response = client.delete("/delete_course", query_string={"course_id": "course-123", "requester_id": "req-123"})

    assert response.status_code == 409
    assert response.json["message"] == "Cannot delete course with assignments"

def test_delete_all_assignments_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_commit = mocker.patch("routes.course.db.session.commit")
    mocker.patch("routes.course.get_user_course_role", return_value="instructor")

    mock_query.return_value.filter_by.return_value.all.return_value = [mocker.Mock(id="assignment-1")]

    response = client.delete("/delete_all_assignments", query_string={"course_id": "course-123", "requester_id": "req-123"})

    assert response.status_code == 200
    assert response.json == "Assignments deleted successfully"
    mock_commit.assert_called()


def test_delete_all_assignments_not_found(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mocker.patch("routes.course.get_user_course_role", return_value="instructor")
    mock_query.return_value.filter_by.return_value.all.return_value = []

    response = client.delete("/delete_all_assignments", query_string={"course_id": "course-123", "requester_id": "req-123"})

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
    mocker.patch("routes.course.get_user_course_role", return_value="instructor")

    enrollment = mocker.Mock()
    mock_query.return_value.filter_by.return_value.first.return_value = enrollment

    payload = {
        "student_id": "student-123",
        "course_id": "course-123",
        "new_role": "TA",
        "requester_id": "req-123"
    }

    response = client.post("/update_role", json=payload)

    assert response.status_code == 200
    assert response.json["role"] == "ta"
    assert enrollment.role == "ta"
    mock_commit.assert_called_once()

def test_update_role_not_found(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mocker.patch("routes.course.get_user_course_role", return_value="instructor")
    mock_query.return_value.filter_by.return_value.first.return_value = None  # Enrollment not found

    payload = {
        "student_id": "student-123",
        "course_id": "course-123",
        "new_role": "TA",
        "requester_id": "req-123"
    }

    response = client.post("/update_role", json=payload)

    assert response.status_code == 404
    assert response.json["message"] == "Enrollment not found"

import io

def test_create_enrollment_csv_success(client, mocker):
    file_content = "Email\nstudent1@test.com\nstudent2@test.com"
    mock_file = (io.BytesIO(file_content.encode()), "students.csv")

    mock_user_1 = mocker.Mock()
    mock_user_1.id = "uuid-1"
    mock_user_2 = mocker.Mock()
    mock_user_2.id = "uuid-2"

    mock_query = mocker.patch("routes.course.User.query")
    mock_query.filter_by.return_value.first.side_effect = [mock_user_1, mock_user_2]

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
    mock_create_bulk.assert_called_once_with({
        "course_id": "course-123",
        "student_ids": ["uuid-1", "uuid-2"],
        "role": "student"
    })


def test_create_enrollment_csv_missing_file(client, mocker):
    response = client.post("/create_enrollment_csv", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert response.json["message"] == "Missing file part"

def test_get_user_enrollments_success(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query.return_value.filter_by.return_value.all.return_value = [mocker.Mock(course_id="course-123", role="student")]
    mock_query.return_value.filter.return_value = [mocker.Mock(id="course-123", name="CS101")]
    mock_schema = mocker.patch("routes.course.CourseSchema")
    mock_schema.return_value.dump.return_value = [{"id": "course-123", "name": "CS101"}]

    response = client.get("/get_user_enrollments", query_string={"user_id": "user-123"})

    assert response.status_code == 200
    assert response.json == [{"id": "course-123", "name": "CS101", "enrollment_role": "student"}]

def test_get_user_enrollments_missing_user_id(client):
    response = client.get("/get_user_enrollments")
    assert response.status_code == 400
    assert response.json["message"] == "Missing user_id argument"

from types import SimpleNamespace

def test_get_course_enrollment_success(client, mocker):
    # Mock the query chain used in the new route (query -> join -> filter)
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query_instance = mock_query.return_value
    mock_join = mock_query_instance.join.return_value
    mock_filter = mock_join.filter.return_value
    mock_filter.all.return_value = [
        SimpleNamespace(
            id="student-123",
            name="John Doe",
            email_address="john@example.com",
            role="student"
        )
    ]
    response = client.get("/get_course_enrollment", query_string={"course_id": "course-123"})
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["id"] == "student-123"
    assert data[0]["name"] == "John Doe"
    assert data[0]["role"] == "student"

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

    mock_course = mocker.Mock(
        id="course-123",
        name="CS101",
        default_ai_provider="openai",
        default_ai_model="gpt-4o-mini",
        default_feedback_style="hint-based",
        default_ai_temperature=0.5,
        openai_api_key="encrypted-key",
        gemini_api_key="",
        claude_api_key="",
    )

    mock_query.return_value.filter_by.return_value.first.return_value = mock_course

    mock_schema = mocker.patch("routes.course.CourseSchema")
    mock_schema.return_value.dump.return_value = {
        "id": "course-123",
        "name": "CS101",
    }

    response = client.get("/get_course_info", query_string={"course_id": "course-123"})

    assert response.status_code == 200
    assert response.json == [
        {
            "id": "course-123",
            "name": "CS101",
            "default_ai_provider": "openai",
            "default_ai_model": "gpt-4o-mini",
            "default_feedback_style": "hint-based",
            "default_ai_temperature": 0.5,
            "has_openai_api_key": True,
            "has_gemini_api_key": False,
            "has_claude_api_key": False,
        }
    ]

    assert "openai_api_key_value" not in response.json[0]
    assert "gemini_api_key_value" not in response.json[0]
    assert "claude_api_key_value" not in response.json[0]

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
    mocker.patch("routes.course.db.session.rollback")

    data = {
        "course_id": "course-1",
        "student_ids": ["a", "b"]
    }

    result = create_enrollment_bulk(data)
    failed_ids = {f["id"] for f in result["failed_enrollments"]}
    assert failed_ids == {"a", "b"}

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
    mocker.patch("routes.course.get_user_course_role", return_value="instructor")

    response = client.delete("/delete_course", query_string={"course_id": "course-123", "requester_id": "req-123"})
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

def test_test_ai_api_key_openai_success(client, mocker):
    mock_openai_class = mocker.patch("routes.course.OpenAI")
    mock_openai_client = mocker.Mock()
    mock_openai_client.models.list.return_value = mocker.Mock()
    mock_openai_class.return_value = mock_openai_client

    response = client.post(
        "/test_ai_api_key",
        json={
            "provider": "openai",
            "api_key": "test-openai-key",
        },
    )

    assert response.status_code == 200
    assert response.json["message"] == "OpenAI API key is valid"
    assert response.json["provider"] == "openai"

    mock_openai_class.assert_called_once_with(api_key="test-openai-key")
    mock_openai_client.models.list.assert_called_once()


def test_test_ai_api_key_gemini_success(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": []}

    mock_get = mocker.patch("routes.course.requests.get", return_value=mock_response)

    response = client.post(
        "/test_ai_api_key",
        json={
            "provider": "gemini",
            "api_key": "test-gemini-key",
        },
    )

    assert response.status_code == 200
    assert response.json["message"] == "Gemini API key is valid"
    assert response.json["provider"] == "gemini"

    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs["params"] == {"key": "test-gemini-key"}


def test_test_ai_api_key_claude_success(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}

    mock_get = mocker.patch("routes.course.requests.get", return_value=mock_response)

    response = client.post(
        "/test_ai_api_key",
        json={
            "provider": "claude",
            "api_key": "test-claude-key",
        },
    )

    assert response.status_code == 200
    assert response.json["message"] == "Claude API key is valid"
    assert response.json["provider"] == "claude"

    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs["headers"]["x-api-key"] == "test-claude-key"
    assert mock_get.call_args.kwargs["headers"]["anthropic-version"] == "2023-06-01"


def test_test_ai_api_key_missing_saved_key_returns_400(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")

    mock_course = mocker.Mock(
        id="course-123",
        openai_api_key="",
        gemini_api_key="",
        claude_api_key="",
    )

    mock_query.return_value.filter_by.return_value.first.return_value = mock_course

    response = client.post(
        "/test_ai_api_key",
        json={
            "course_id": "course-123",
            "provider": "gemini",
        },
    )

    assert response.status_code == 400


def test_test_ai_model_openai_success(client, mocker):
    mock_message = mocker.Mock()
    mock_message.content = '{"insights":["Model test passed."],"annotations":[]}'

    mock_choice = mocker.Mock()
    mock_choice.message = mock_message

    mock_completion = mocker.Mock()
    mock_completion.choices = [mock_choice]

    mock_openai_client = mocker.Mock()
    mock_openai_client.chat.completions.create.return_value = mock_completion

    mock_openai_class = mocker.patch(
        "routes.course.OpenAI",
        return_value=mock_openai_client,
    )

    response = client.post(
        "/test_ai_model",
        json={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "test-openai-key",
        },
    )

    assert response.status_code == 200
    assert response.json["provider"] == "openai"
    assert response.json["model"] == "gpt-4o-mini"

    mock_openai_class.assert_called_once_with(api_key="test-openai-key")
    mock_openai_client.chat.completions.create.assert_called_once()


def test_test_ai_model_gemini_success(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"insights":["Model test passed."],"annotations":[]}'
                        }
                    ]
                }
            }
        ]
    }

    mock_post = mocker.patch("routes.course.requests.post", return_value=mock_response)

    response = client.post(
        "/test_ai_model",
        json={
            "provider": "gemini",
            "model": "gemini-1.5-flash",
            "api_key": "test-gemini-key",
        },
    )

    assert response.status_code == 200
    assert response.json["provider"] == "gemini"
    assert response.json["model"] == "gemini-1.5-flash"

    mock_post.assert_called_once()
    assert "gemini-1.5-flash:generateContent" in mock_post.call_args.args[0]
    assert mock_post.call_args.kwargs["params"] == {"key": "test-gemini-key"}


def test_test_ai_model_gemini_uses_feedback_generation_config(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"insights":["Model test passed."],"annotations":[]}'
                        }
                    ]
                }
            }
        ]
    }

    mock_post = mocker.patch("routes.course.requests.post", return_value=mock_response)

    response = client.post(
        "/test_ai_model",
        json={
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "api_key": "test-gemini-key",
        },
    )

    assert response.status_code == 200

    generation_config = mock_post.call_args.kwargs["json"]["generationConfig"]
    assert generation_config["maxOutputTokens"] == 1600
    assert generation_config["responseMimeType"] == "application/json"
    assert generation_config["thinkingConfig"] == {"thinkingBudget": 0}


def test_test_ai_model_gemini_invalid_json_returns_error(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "This model can chat, but did not return JSON."
                        }
                    ]
                }
            }
        ]
    }

    mocker.patch("routes.course.requests.post", return_value=mock_response)

    response = client.post(
        "/test_ai_model",
        json={
            "provider": "gemini",
            "model": "gemini-1.5-flash",
            "api_key": "test-gemini-key",
        },
    )

    assert response.status_code == 400
    assert "valid JSON feedback" in response.json["error"]


def test_test_ai_model_gemini_unavailable_returns_error(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 503
    mock_response.text = (
        '{"error":{"message":"This model is currently experiencing high demand."}}'
    )

    mocker.patch("routes.course.requests.post", return_value=mock_response)

    response = client.post(
        "/test_ai_model",
        json={
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "api_key": "test-gemini-key",
        },
    )

    assert response.status_code == 503
    assert "Selected Gemini model cannot be used" in response.json["error"]


def test_test_ai_model_claude_success(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [
            {
                "type": "text",
                "text": '{"insights":["Model test passed."],"annotations":[]}',
            }
        ]
    }

    mock_post = mocker.patch("routes.course.requests.post", return_value=mock_response)

    response = client.post(
        "/test_ai_model",
        json={
            "provider": "claude",
            "model": "claude-3-5-sonnet-20241022",
            "api_key": "test-claude-key",
        },
    )

    assert response.status_code == 200
    assert response.json["provider"] == "claude"
    assert response.json["model"] == "claude-3-5-sonnet-20241022"

    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["headers"]["x-api-key"] == "test-claude-key"
    assert (
        mock_post.call_args.kwargs["json"]["model"]
        == "claude-3-5-sonnet-20241022"
    )


def test_test_ai_model_claude_unavailable_returns_error(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 404
    mock_response.text = (
        '{"type":"error","error":{"type":"not_found_error",'
        '"message":"Claude Fable 5 is not available."}}'
    )

    mocker.patch("routes.course.requests.post", return_value=mock_response)

    response = client.post(
        "/test_ai_model",
        json={
            "provider": "claude",
            "model": "claude-fable-5",
            "api_key": "test-claude-key",
        },
    )

    assert response.status_code == 404
    assert "Selected Claude model cannot be used" in response.json["error"]


def test_fetch_ai_models_gemini_filters_and_sorts_models(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {
                "name": "models/gemini-2.5-flash",
                "supportedGenerationMethods": ["generateContent"],
            },
            {
                "name": "models/gemini-1.5-flash",
                "supportedGenerationMethods": ["generateContent"],
            },
            {
                "name": "models/text-embedding-004",
                "supportedGenerationMethods": ["embedContent"],
            },
        ]
    }

    mocker.patch("routes.course.requests.get", return_value=mock_response)

    response = client.post(
        "/fetch_ai_models",
        json={
            "provider": "gemini",
            "api_key": "test-gemini-key",
        },
    )

    assert response.status_code == 200
    assert response.json["models"][0] == "gemini-1.5-flash"
    assert "gemini-2.5-flash" in response.json["models"]
    assert "text-embedding-004" not in response.json["models"]


def test_fetch_ai_models_claude_filters_unavailable_models(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "claude-fable-5"},
            {"id": "claude-mythos-5"},
            {"id": "claude-3-5-sonnet-20241022"},
            {"id": "claude-3-5-haiku-20241022"},
        ]
    }

    mocker.patch("routes.course.requests.get", return_value=mock_response)

    response = client.post(
        "/fetch_ai_models",
        json={
            "provider": "claude",
            "api_key": "test-claude-key",
        },
    )

    assert response.status_code == 200
    assert "claude-fable-5" not in response.json["models"]
    assert "claude-mythos-5" not in response.json["models"]
    assert response.json["models"][0] == "claude-3-5-sonnet-20241022"

def test_test_ai_api_key_missing_provider_returns_400(client):
    response = client.post(
        "/test_ai_api_key",
        json={
            "api_key": "test-key",
        },
    )

    assert response.status_code == 400
    assert response.json["message"] == "Missing provider"


def test_test_ai_api_key_unsupported_provider_returns_400(client):
    response = client.post(
        "/test_ai_api_key",
        json={
            "provider": "llama",
            "api_key": "test-key",
        },
    )

    assert response.status_code == 400
    assert response.json["message"] == "Unsupported AI provider"


def test_test_ai_api_key_uses_saved_gemini_key(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_decrypt = mocker.patch(
        "routes.course.decrypt_api_key",
        return_value="decrypted-gemini-key",
    )

    mock_course = mocker.Mock(
        id="course-123",
        openai_api_key="",
        gemini_api_key="encrypted-gemini-key",
        claude_api_key="",
    )

    mock_query.return_value.filter_by.return_value.first.return_value = mock_course

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": []}

    mock_get = mocker.patch("routes.course.requests.get", return_value=mock_response)

    response = client.post(
        "/test_ai_api_key",
        json={
            "course_id": "course-123",
            "provider": "gemini",
        },
    )

    assert response.status_code == 200
    assert response.json["message"] == "Gemini API key is valid"

    mock_decrypt.assert_called_once_with("encrypted-gemini-key")
    assert mock_get.call_args.kwargs["params"] == {"key": "decrypted-gemini-key"}


def test_test_ai_api_key_saved_course_not_found_returns_404(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    response = client.post(
        "/test_ai_api_key",
        json={
            "course_id": "missing-course",
            "provider": "openai",
        },
    )

    assert response.status_code == 404
    assert response.json["message"] == "Course not found"


def test_test_ai_model_missing_provider_returns_400(client):
    response = client.post(
        "/test_ai_model",
        json={
            "model": "gpt-4o-mini",
            "api_key": "test-key",
        },
    )

    assert response.status_code == 400
    assert response.json["message"] == "Missing provider"


def test_test_ai_model_missing_model_returns_400(client):
    response = client.post(
        "/test_ai_model",
        json={
            "provider": "openai",
            "api_key": "test-key",
        },
    )

    assert response.status_code == 400
    assert response.json["message"] == "Missing model"


def test_test_ai_model_unsupported_provider_returns_400(client):
    response = client.post(
        "/test_ai_model",
        json={
            "provider": "llama",
            "model": "llama-test-model",
            "api_key": "test-key",
        },
    )

    assert response.status_code == 400
    assert response.json["message"] == "Unsupported AI provider"


def test_test_ai_model_uses_saved_claude_key(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_decrypt = mocker.patch(
        "routes.course.decrypt_api_key",
        return_value="decrypted-claude-key",
    )

    mock_course = mocker.Mock(
        id="course-123",
        openai_api_key="",
        gemini_api_key="",
        claude_api_key="encrypted-claude-key",
    )

    mock_query.return_value.filter_by.return_value.first.return_value = mock_course

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [
            {
                "type": "text",
                "text": '{"insights":["Model test passed."],"annotations":[]}',
            }
        ]
    }

    mock_post = mocker.patch("routes.course.requests.post", return_value=mock_response)

    response = client.post(
        "/test_ai_model",
        json={
            "course_id": "course-123",
            "provider": "claude",
            "model": "claude-3-5-sonnet-20241022",
        },
    )

    assert response.status_code == 200
    assert response.json["provider"] == "claude"
    assert response.json["model"] == "claude-3-5-sonnet-20241022"

    mock_decrypt.assert_called_once_with("encrypted-claude-key")
    assert mock_post.call_args.kwargs["headers"]["x-api-key"] == "decrypted-claude-key"


def test_fetch_ai_models_missing_provider_returns_400(client):
    response = client.post(
        "/fetch_ai_models",
        json={
            "api_key": "test-key",
        },
    )

    assert response.status_code == 400
    assert response.json["message"] == "Missing provider"


def test_fetch_ai_models_unsupported_provider_returns_400(client):
    response = client.post(
        "/fetch_ai_models",
        json={
            "provider": "llama",
            "api_key": "test-key",
        },
    )

    assert response.status_code == 400
    assert response.json["message"] == "Unsupported AI provider"


def test_fetch_ai_models_openai_filters_unsupported_models(client, mocker):
    mock_gpt_model = mocker.Mock()
    mock_gpt_model.id = "gpt-4o-mini"

    mock_audio_model = mocker.Mock()
    mock_audio_model.id = "gpt-4o-audio-preview"

    mock_realtime_model = mocker.Mock()
    mock_realtime_model.id = "gpt-4o-realtime-preview"

    mock_search_model = mocker.Mock()
    mock_search_model.id = "gpt-4o-mini-search-preview"

    mock_o_model_full = mocker.Mock()
    mock_o_model_full.id = "o3"

    mock_o_model = mocker.Mock()
    mock_o_model.id = "o3-mini"

    mock_embedding_model = mocker.Mock()
    mock_embedding_model.id = "text-embedding-3-small"

    mock_other_model = mocker.Mock()
    mock_other_model.id = "whisper-1"

    mock_models_response = mocker.Mock()
    mock_models_response.data = [
        mock_embedding_model,
        mock_gpt_model,
        mock_audio_model,
        mock_realtime_model,
        mock_search_model,
        mock_other_model,
        mock_o_model_full,
        mock_o_model,
    ]

    mock_openai_client = mocker.Mock()
    mock_openai_client.models.list.return_value = mock_models_response

    mocker.patch("routes.course.OpenAI", return_value=mock_openai_client)

    response = client.post(
        "/fetch_ai_models",
        json={
            "provider": "openai",
            "api_key": "test-openai-key",
        },
    )

    assert response.status_code == 200
    assert "gpt-4o-mini" in response.json["models"]
    assert "gpt-4o-audio-preview" not in response.json["models"]
    assert "gpt-4o-realtime-preview" not in response.json["models"]
    assert "gpt-4o-mini-search-preview" not in response.json["models"]
    assert "o3" not in response.json["models"]
    assert "o3-mini" not in response.json["models"]
    assert "text-embedding-3-small" not in response.json["models"]
    assert "whisper-1" not in response.json["models"]


def test_fetch_ai_models_gemini_filters_preview_and_experimental_models(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {
                "name": "models/gemini-2.5-flash",
                "supportedGenerationMethods": ["generateContent"],
            },
            {
                "name": "models/gemini-2.5-pro-preview-06-05",
                "supportedGenerationMethods": ["generateContent"],
            },
            {
                "name": "models/gemini-2.0-flash-exp",
                "supportedGenerationMethods": ["generateContent"],
            },
            {
                "name": "models/gemini-2.5-flash-preview-tts",
                "supportedGenerationMethods": ["generateContent"],
            },
        ]
    }

    mocker.patch("routes.course.requests.get", return_value=mock_response)

    response = client.post(
        "/fetch_ai_models",
        json={
            "provider": "gemini",
            "api_key": "test-gemini-key",
        },
    )

    assert response.status_code == 200
    assert response.json["models"] == ["gemini-2.5-flash"]


def test_fetch_ai_models_gemini_api_error_returns_provider_error(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 403
    mock_response.text = '{"error":{"message":"API key not valid."}}'

    mocker.patch("routes.course.requests.get", return_value=mock_response)

    response = client.post(
        "/fetch_ai_models",
        json={
            "provider": "gemini",
            "api_key": "bad-gemini-key",
        },
    )

    assert response.status_code == 403
    assert "API key not valid" in response.json["error"]


def test_fetch_ai_models_claude_api_error_returns_provider_error(client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 401
    mock_response.text = '{"type":"error","error":{"message":"invalid x-api-key"}}'

    mocker.patch("routes.course.requests.get", return_value=mock_response)

    response = client.post(
        "/fetch_ai_models",
        json={
            "provider": "claude",
            "api_key": "bad-claude-key",
        },
    )

    assert response.status_code == 401
    assert "invalid x-api-key" in response.json["error"]


def test_update_ai_settings_updates_openai_key_and_defaults(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_encrypt = mocker.patch(
        "routes.course.encrypt_api_key",
        return_value="encrypted-openai-key",
    )
    mock_commit = mocker.patch("routes.course.db.session.commit")
    mocker.patch("routes.course.get_user_course_role", return_value="instructor")

    mock_course = mocker.Mock()
    mock_query.return_value.filter_by.return_value.first.return_value = mock_course

    response = client.put(
        "/update_ai_settings",
        json={
            "course_id": "course-123",
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "api_key": "plain-openai-key",
            "feedback_style": "balanced",
            "temperature": 0.3,
            "requester_id": "req-123",
        },
    )

    assert response.status_code == 200
    assert response.json["message"] == "AI settings updated successfully"

    assert mock_course.default_ai_provider == "openai"
    assert mock_course.default_ai_model == "gpt-4o-mini"
    assert mock_course.default_feedback_style == "balanced"
    assert mock_course.default_ai_temperature == 0.3
    assert mock_course.openai_api_key == "encrypted-openai-key"

    mock_encrypt.assert_called_once_with("plain-openai-key")
    mock_commit.assert_called_once()


def test_update_ai_settings_invalid_temperature_returns_400(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mocker.patch("routes.course.get_user_course_role", return_value="instructor")

    mock_course = mocker.Mock()
    mock_query.return_value.filter_by.return_value.first.return_value = mock_course

    response = client.put(
        "/update_ai_settings",
        json={
            "course_id": "course-123",
            "provider": "openai",
            "temperature": "hot",
            "requester_id": "req-123",
        },
    )

    assert response.status_code == 400
    assert response.json["message"] == "Invalid temperature"


def test_update_ai_settings_temperature_out_of_range_returns_400(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mocker.patch("routes.course.get_user_course_role", return_value="instructor")

    mock_course = mocker.Mock()
    mock_query.return_value.filter_by.return_value.first.return_value = mock_course

    response = client.put(
        "/update_ai_settings",
        json={
            "course_id": "course-123",
            "provider": "openai",
            "temperature": 1.5,
            "requester_id": "req-123",
        },
    )

    assert response.status_code == 400
    assert response.json["message"] == "Temperature must be between 0 and 1"


def test_update_ai_settings_unsupported_provider_without_api_key_returns_400(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mock_commit = mocker.patch("routes.course.db.session.commit")
    mocker.patch("routes.course.get_user_course_role", return_value="instructor")

    mock_course = mocker.Mock()
    mock_query.return_value.filter_by.return_value.first.return_value = mock_course

    response = client.put(
        "/update_ai_settings",
        json={
            "course_id": "course-123",
            "provider": "llama",
            "model_name": "llama-test-model",
            "requester_id": "req-123",
        },
    )

    assert response.status_code == 400
    assert response.json["message"] == "Unsupported AI provider"
    mock_commit.assert_not_called()


def test_update_ai_settings_unsupported_provider_for_api_key_returns_400(client, mocker):
    mock_query = mocker.patch("routes.course.db.session.query")
    mocker.patch("routes.course.get_user_course_role", return_value="instructor")

    mock_course = mocker.Mock()
    mock_query.return_value.filter_by.return_value.first.return_value = mock_course

    response = client.put(
        "/update_ai_settings",
        json={
            "course_id": "course-123",
            "provider": "llama",
            "api_key": "plain-key",
            "requester_id": "req-123",
        },
    )

    assert response.status_code == 400
    assert response.json["message"] == "Unsupported AI provider"
