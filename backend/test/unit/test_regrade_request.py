import uuid
import pytest
from api import create_app, db  # adjust if your factory lives elsewhere
from types import SimpleNamespace


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


def _login_as(client, user_id):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def _mock_course_role(mocker, role="instructor"):
    return mocker.patch("util.auth.get_user_course_role", return_value=role)

# Test cases

# Test cases for send_regrade_request


def test_send_regrade_request_success(client, mocker):
    payload = {"submission_id": "sub1", "justification": "Please re‑check."}

    mocker.patch("routes.regrade_request.db.session.add")
    mocker.patch("routes.regrade_request.db.session.commit")
    mock_query = mocker.patch("routes.regrade_request.db.session.query")
    mock_query.return_value.filter_by.return_value = ["dummy-row"]

    mock_schema = mocker.patch("routes.regrade_request.UserSchema")
    mock_schema.return_value.dump.return_value = [{"id": "req‑123"}]

    mocker.patch("routes.regrade_request.uuid.uuid4", return_value=uuid.UUID(int=1))

    res = client.post("/send_regrade_request", json=payload)
    assert res.status_code == 200
    assert res.get_json() == {"id": "req‑123"}


# Test cases for get_regrade_request


def test_get_regrade_request_missing_id(client):
    res = client.get("/get_regrade_request")
    assert res.status_code == 400
    assert res.get_json()["message"] == "No submission id passed"


def test_get_regrade_request_no_submission(client, mocker):
    sub_query = mocker.patch("routes.regrade_request.Submission.query")
    sub_query.filter_by.return_value.first.return_value = None

    res = client.get("/get_regrade_request?submission_id=sub404")
    assert res.status_code == 404
    assert res.get_json()["message"] == "No such submission"


def test_get_regrade_request_no_request(client, mocker):
    sub_query = mocker.patch("routes.regrade_request.Submission.query")
    sub_query.filter_by.return_value.first.return_value = object()

    req_query = mocker.patch("routes.regrade_request.RegradeRequest.query")
    req_query.filter_by.return_value.first.return_value = None

    res = client.get("/get_regrade_request?submission_id=sub1")
    assert res.status_code == 404
    assert res.get_json()["message"] == "No regrade request found"


def test_get_regrade_request_success(client, mocker):
    fake_sub = object()
    fake_req = mocker.Mock(justification="Because…", reviewed=False)

    # Submission exists
    sub_query = mocker.patch("routes.regrade_request.Submission.query")  
    sub_query.filter_by.return_value.first.return_value = fake_sub
    
    # RegradeRequest exists
    req_query = mocker.patch("routes.regrade_request.RegradeRequest.query")
    req_query.filter_by.return_value.first.return_value = fake_req

    mocker.patch("routes.regrade_request.SubmissionSchema") \
          .return_value.dump.return_value = {"id": "sub1"}

    res = client.get("/get_regrade_request?submission_id=sub1")
    assert res.status_code == 200
    assert res.get_json() == {
        "submission": {"id": "sub1"},
        "justification": "Because…",
        "reviewed": False,
    }


# Test cases for check_regrade_request


def test_check_regrade_request_false(client, mocker):
    mocker.patch("routes.regrade_request.db.session.query").return_value.filter_by.return_value.first.return_value = None
    res = client.post("/check_regrade_request", json={"submission_id": "subX"})
    assert res.status_code == 200
    assert res.get_json() == {"has_request": False}


def test_check_regrade_request_true(client, mocker):
    mocker.patch("routes.regrade_request.db.session.query").return_value.filter_by.return_value.first.return_value = object()
    res = client.post("/check_regrade_request", json={"submission_id": "sub1"})
    assert res.status_code == 200
    assert res.get_json() == {"has_request": True}


# Test cases for delete_regrade_request


def test_delete_regrade_request(client, mocker):
    mocker.patch("routes.regrade_request.RegradeRequest.query.filter_by")
    mocker.patch("routes.regrade_request.db.session.commit")
    res = client.post("/delete_regrade_request", json={"submission_id": "sub1"})
    assert res.status_code == 200
    assert res.get_json()["message"] == "Regrade request deleted"


# Test cases for set_reviewed


def test_set_reviewed(client, mocker):
    mock_entry = mocker.Mock()
    mocker.patch("routes.regrade_request.db.session.query").return_value.filter_by.return_value.first.return_value = mock_entry
    commit = mocker.patch("routes.regrade_request.db.session.commit")
    _mock_course_role(mocker)
    _login_as(client, "instructor-uuid")
    res = client.post("/set_reviewed", json={"submission_id": "sub1"})
    assert res.status_code == 200
    assert res.get_json()["message"] == "Review updated successfully"
    assert mock_entry.reviewed is True
    commit.assert_called_once()


# Test cases for update_grade


def test_update_grade_success(client, mocker):
    fake_sub = SimpleNamespace(score=80, assignment_id="assign1")

    sub_query = mocker.patch("routes.regrade_request.Submission.query")
    # filter_by(...).first() should give back the fake submission
    sub_query.filter_by.return_value.first.return_value = fake_sub

    mock_query = mocker.patch("routes.regrade_request.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = SimpleNamespace(
        id="assign1", course_id="course-uuid"
    )

    commit = mocker.patch("routes.regrade_request.db.session.commit")
    _mock_course_role(mocker)
    _login_as(client, "instructor-uuid")

    res = client.post("/update_grade", json={"submission_id": "sub1", "new_grade": 95})
    assert res.status_code == 200
    assert fake_sub.score == 95
    assert res.get_json()["message"] == "Grade updated successfully"
    commit.assert_called_once()


def test_update_grade_missing_fields(client):
    res = client.post("/update_grade", json={"submission_id": "sub1"})
    assert res.status_code == 400
    assert res.get_json()["message"] == "Missing submission_id or new_grade"


# Test cases for get_student_regrade_requests


def test_get_student_regrade_requests_missing_student(client):
    res = client.get("/get_student_regrade_requests?course_id=course1")
    assert res.status_code == 400
    assert res.get_json()["message"] == "Missing student_id"


def test_get_student_regrade_requests_missing_course(client):
    res = client.get("/get_student_regrade_requests?student_id=stu1")
    assert res.status_code == 400
    assert res.get_json()["message"] == "Missing course_id"


def test_get_student_regrade_requests_success(client, mocker):
    req = SimpleNamespace(id="req1", submission_id="sub1",
                          justification="Fix", reviewed=False)
    submission = SimpleNamespace(id="sub1", assignment_id="assign1", student_id="stu1")
    assignment = SimpleNamespace(id="assign1", name="A1")
    student = SimpleNamespace(id="stu1", name="Stu")

    def query_side_effect(model):
        name = getattr(model, "__name__", "")
        if name == "RegradeRequest":
            q = mocker.Mock()
            q.join.return_value = q
            q.filter.return_value = q
            q.all.return_value = [req]
            return q
        if name == "Submission":
            q = mocker.Mock()
            q.filter_by.return_value.first.return_value = submission
            return q
        if name == "Assignment":
            q = mocker.Mock()
            q.filter_by.return_value.first.return_value = assignment
            return q
        if name == "User":
            q = mocker.Mock()
            q.filter_by.return_value.first.return_value = student
            return q
        return mocker.Mock()

    mocker.patch("routes.regrade_request.db.session.query", side_effect=query_side_effect)

    res = client.get("/get_student_regrade_requests?student_id=stu1&course_id=course1")
    assert res.status_code == 200
    assert res.get_json() == [{
        "regradeRequestId": "req1",
        "assignmentName": "A1",
        "studentName": "Stu",
        "justification": "Fix",
        "assignmentId": "assign1",
        "studentId": "stu1",
        "reviewed": False,
    }]


# Test cases for get_instructor_regrade_requests


def test_set_reviewed_success_with_simple_namespace(client, mocker):
    entry = SimpleNamespace(reviewed=False, submission_id="sub1")
    mocker.patch("routes.regrade_request.db.session.query") \
          .return_value.filter_by.return_value.first.side_effect = [
        entry,
        SimpleNamespace(id="sub1", assignment_id="assign1"),
        SimpleNamespace(id="assign1", course_id="course-uuid"),
    ]
    commit = mocker.patch("routes.regrade_request.db.session.commit")
    _mock_course_role(mocker)
    _login_as(client, "instructor-uuid")

    res = client.post("/set_reviewed", json={"submission_id": "sub1"})
    assert res.status_code == 200
    assert entry.reviewed is True
    assert res.get_json()["message"] == "Review updated successfully"
    commit.assert_called_once()

def test_update_grade_no_submission(client, mocker):
    sub_query = mocker.patch("routes.regrade_request.Submission.query")
    sub_query.filter_by.return_value.first.return_value = None
    _login_as(client, "instructor-uuid")

    res = client.post("/update_grade", json={
        "submission_id": "missing-sub",
        "new_grade": 95
    })

    assert res.status_code == 404
    assert res.get_json()["message"] == "No such submission found"

def test_update_grade_invalid_grade(client, mocker):
    fake_sub = SimpleNamespace(score=80, assignment_id="assign1")

    sub_query = mocker.patch("routes.regrade_request.Submission.query")
    sub_query.filter_by.return_value.first.return_value = fake_sub

    mock_query = mocker.patch("routes.regrade_request.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = SimpleNamespace(
        id="assign1", course_id="course-uuid"
    )
    _mock_course_role(mocker)
    _login_as(client, "instructor-uuid")

    res = client.post("/update_grade", json={
        "submission_id": "sub1",
        "new_grade": "bad-grade"
    })

    assert res.status_code == 400
    assert res.get_json()["message"] == "Invalid grade value"

def test_set_reviewed_not_found(client, mocker):
    mocker.patch("routes.regrade_request.db.session.query") \
        .return_value.filter_by.return_value.first.return_value = None
    _login_as(client, "instructor-uuid")

    res = client.post("/set_reviewed", json={"submission_id": "sub404"})

    assert res.status_code == 404
    assert res.get_json()["message"] == "No regrade request found for submission_id: sub404"


# ---------------------------------------------------------------------------
# Negative-path auth tests (session-based guards)
# ---------------------------------------------------------------------------


def test_update_grade_unauthenticated(client):
    res = client.post("/update_grade", json={"submission_id": "sub1", "new_grade": 90})
    assert res.status_code == 401
    assert "Not authenticated" in res.get_json()["message"]


def test_update_grade_student_forbidden(client, mocker):
    fake_sub = SimpleNamespace(score=80, assignment_id="assign1")
    sub_query = mocker.patch("routes.regrade_request.Submission.query")
    sub_query.filter_by.return_value.first.return_value = fake_sub

    mock_query = mocker.patch("routes.regrade_request.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = SimpleNamespace(
        id="assign1", course_id="course-uuid"
    )
    _mock_course_role(mocker, role="student")
    _login_as(client, "student-uuid")

    res = client.post("/update_grade", json={"submission_id": "sub1", "new_grade": 90})

    assert res.status_code == 403
    assert "Only instructors or TAs" in res.get_json()["message"]
    assert fake_sub.score == 80


def test_update_grade_ta_allowed(client, mocker):
    fake_sub = SimpleNamespace(score=80, assignment_id="assign1")
    sub_query = mocker.patch("routes.regrade_request.Submission.query")
    sub_query.filter_by.return_value.first.return_value = fake_sub

    mock_query = mocker.patch("routes.regrade_request.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = SimpleNamespace(
        id="assign1", course_id="course-uuid"
    )
    commit = mocker.patch("routes.regrade_request.db.session.commit")
    _mock_course_role(mocker, role="ta")
    _login_as(client, "ta-uuid")

    res = client.post("/update_grade", json={"submission_id": "sub1", "new_grade": 90})

    assert res.status_code == 200
    assert fake_sub.score == 90.0
    commit.assert_called_once()


def test_get_instructor_regrade_requests_unauthenticated(client):
    res = client.get("/get_instructor_regrade_requests", query_string={"course_id": "course-uuid"})
    assert res.status_code == 401
    assert "Not authenticated" in res.get_json()["message"]


def test_get_instructor_regrade_requests_student_forbidden(client, mocker):
    _mock_course_role(mocker, role="student")
    _login_as(client, "student-uuid")

    res = client.get("/get_instructor_regrade_requests", query_string={"course_id": "course-uuid"})

    assert res.status_code == 403
    assert "Only instructors or TAs" in res.get_json()["message"]


def test_get_instructor_regrade_requests_ta_allowed(client, mocker):
    _mock_course_role(mocker, role="ta")
    mock_query = mocker.patch("routes.regrade_request.db.session.query")
    mock_query.return_value.join.return_value.join.return_value.filter.return_value = []
    _login_as(client, "ta-uuid")

    res = client.get("/get_instructor_regrade_requests", query_string={"course_id": "course-uuid"})

    assert res.status_code == 200
    assert res.get_json() == []


def test_set_reviewed_unauthenticated(client):
    res = client.post("/set_reviewed", json={"submission_id": "sub1"})
    assert res.status_code == 401
    assert "Not authenticated" in res.get_json()["message"]


def test_set_reviewed_student_forbidden(client, mocker):
    entry = SimpleNamespace(reviewed=False, submission_id="sub1")
    mocker.patch("routes.regrade_request.db.session.query") \
        .return_value.filter_by.return_value.first.side_effect = [
        entry,
        SimpleNamespace(id="sub1", assignment_id="assign1"),
        SimpleNamespace(id="assign1", course_id="course-uuid"),
    ]
    _mock_course_role(mocker, role="student")
    _login_as(client, "student-uuid")

    res = client.post("/set_reviewed", json={"submission_id": "sub1"})

    assert res.status_code == 403
    assert "Only instructors or TAs" in res.get_json()["message"]
    assert entry.reviewed is False