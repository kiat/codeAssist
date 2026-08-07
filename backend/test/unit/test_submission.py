import os
import uuid
import pytest
from flask import json
from api import create_app, db
from api.models import Assignment, Submission


from routes.submission import submission

@pytest.fixture
def app():
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        db.create_all()  # Create the tables
        yield app
        db.drop_all()    # Clean up after tests


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(autouse=True)
def mock_verify_student_owner(mocker):
    """Auto-mock session-based auth in submission routes for unit tests."""
    mocker.patch("routes.submission._verify_student_owner")
    mocker.patch("routes.submission._verify_course_staff")


@pytest.fixture
def mock_user_query(mocker):
    """Mock the database query for user lookup."""
    mock_query = mocker.patch("routes.user.db.session.query")
    mock_user_schema = mocker.patch("routes.user.UserSchema")
    return mock_query, mock_user_schema


# Test cases

# Test cases for submission routes


def test_get_submissions_missing_params(client):
    """Test that missing query parameters returns a 400 error."""
    response = client.get("/get_submissions")
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Missing student_id or assignment_id"

def test_get_submissions_not_found(client, mocker):
    """Test /get_submissions returns 404 when no submissions are found."""
    mock_query = mocker.patch("routes.submission.db.session.query")
    mock_query.return_value.filter_by.return_value.all.return_value = []
    
    response = client.get("/get_submissions?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 404
    data = response.get_json()
    assert data["message"] == "No submissions found for the provided student and assignment"


def test_get_submissions_success(client, mocker):
    """Test /get_submissions returns dumped submission data when submissions exist."""
    fake_submissions = [{"id": "sub1", "score": 100}]
    mock_query = mocker.patch("routes.submission.db.session.query")
    mock_query.return_value.filter_by.return_value.all.return_value = fake_submissions

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submissions

    response = client.get("/get_submissions?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == fake_submissions


# Tests for latest submission retrieval


def test_get_latest_submission_missing_params(client):
    """Test that missing parameters in /get_latest_submission returns 400."""
    response = client.get("/get_latest_submission")
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Missing student_id or assignment_id"


def test_get_latest_submission_success(client, mocker):
    """Test /get_latest_submission returns the latest submission data."""
    fake_submission = {"id": "sub1", "score": 100}
    mock_model = mocker.patch.object(Submission, "query", create=True)
    mock_model.filter_by.return_value.order_by.return_value.first.return_value = fake_submission

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submission

    response = client.get("/get_latest_submission?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == fake_submission


def test_get_latest_submission_not_found(client, mocker):
    """Test /get_latest_submission returns a message when no submission is found."""
    mock_model = mocker.patch.object(Submission, "query", create=True)
    mock_model.filter_by.return_value.order_by.return_value.first.return_value = None

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = None

    response = client.get("/get_latest_submission?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == {"message": "No submissions found", "data": None}


# Tests for deleting a submission


def test_delete_submission_missing_id(client):
    """Test /delete_submission returns error when submission_id is missing."""
    response = client.delete("/delete_submission")
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Missing submission_id"


# Tests for activating a submission


def test_activate_submission_missing_params(client):
    """Test /activate_submission returns error if required fields are missing."""
    payload = {"submission_id": "sub1", "student_id": "stu1"}  # missing assignment_id
    response = client.post("/activate_submission", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Missing submission_id, student_id, or assignment_id"


def test_activate_submission_success(client, mocker):
    """Test /activate_submission successfully activates a submission."""
    payload = {"submission_id": "sub1", "student_id": "stu1", "assignment_id": "assgn1"}

    # Patch the query call chain used in the route.
    # Here we simulate that the query returns an object that supports update()
    fake_old_query = mocker.patch("routes.submission.db.session.query")
    fake_old = mocker.Mock()
    fake_old.update.return_value = None
    fake_old_query.return_value.filter_by.return_value = fake_old

    mock_commit = mocker.patch("routes.submission.db.session.commit")

    response = client.post("/activate_submission", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Submission activated successfully"
    mock_commit.assert_called_once()


# Tests for retrieving results


def test_get_results_success(client, mocker):
    """Test /get_results returns submission results for a valid user email."""
    fake_student = mocker.Mock()
    fake_student.id = "stu1"
    fake_submission_data = [{"id": "sub1", "score": 100}]

    # We need to differentiate between the two query calls:
    # one for User and one for Submission.
    def fake_query(model):
        dummy = mocker.Mock()
        if model.__name__ == "User":
            dummy.filter_by.return_value.first.return_value = fake_student
        elif model.__name__ == "Submission":
            dummy.filter_by.return_value.order_by.return_value.limit.return_value = fake_submission_data
        return dummy

    mocker.patch("routes.submission.db.session.query", side_effect=fake_query)

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submission_data

    response = client.get("/get_results?email=test@example.com&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == fake_submission_data


# Tests for testing submission details


def test_get_submission_details_missing_id(client):
    """Test /get_submission_details returns error when submission_id is missing."""
    response = client.get("/get_submission_details")
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Missing submission id"


def test_get_submission_details_success(client, mocker):
    """Test /get_submission_details returns submission details when found."""
    # Mock submission with student_id and assignment_id for _verify_student_owner
    fake_submission = mocker.Mock()
    fake_submission.id = "sub1"
    fake_submission.student_id = "stu1"
    fake_submission.assignment_id = "assgn1"
    fake_submission.score = 100
    fake_submission_dumped = {"id": "sub1", "score": 100}
    dummy_query = mocker.patch("routes.submission.db.session.query")
    dummy_query.return_value.filter_by.return_value.first.return_value = fake_submission

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submission_dumped

    response = client.get("/get_submission_details?submission_id=sub1")
    assert response.status_code == 200
    assert response.get_json() == fake_submission_dumped


def test_rerun_submission_autograder_missing_id(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "stu1"
    response = client.post("/rerun_submission_autograder", json={})

    assert response.status_code == 400
    assert response.get_json()["message"] == "Missing submission_id"


def test_rerun_submission_autograder_requires_configured_autograder(client, mocker):
    with client.session_transaction() as sess:
        sess["user_id"] = "stu1"

    existing_submission = mocker.Mock()
    existing_submission.id = "sub1"
    existing_submission.assignment_id = "assgn1"

    assignment = mocker.Mock()
    assignment.id = "assgn1"
    assignment.autograder_image_name = ""

    def fake_get(model, item_id):
        if model.__name__ == "Submission":
            return existing_submission
        if model.__name__ == "Assignment":
            return assignment
        return None

    mocker.patch("routes.submission.db.session.get", side_effect=fake_get)

    response = client.post(
        "/rerun_submission_autograder",
        json={"submission_id": "sub1"},
    )

    assert response.status_code == 400
    assert "No autograder configured" in response.get_json()["message"]


#  Tests for getting active submission


def test_get_active_submission_success(client, mocker):
    """Test /get_active_submission returns active submission details."""
    fake_submission = {"id": "sub1", "active": True}
    dummy_query = mocker.patch("routes.submission.db.session.query")
    dummy_query.return_value.filter_by.return_value.first.return_value = fake_submission

    fake_schema = mocker.patch("routes.submission.SubmissionSchema")
    fake_schema.return_value.dump.return_value = fake_submission

    response = client.get("/get_active_submission?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 200
    assert response.get_json() == fake_submission


def test_get_active_submission_not_found(client, mocker):
    """Test /get_active_submission returns message when no active submission exists."""
    dummy_query = mocker.patch("routes.submission.db.session.query")
    dummy_query.return_value.filter_by.return_value.first.return_value = None

    response = client.get("/get_active_submission?student_id=stu1&assignment_id=assgn1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "No active submission found"
    assert data["data"] is None


# Edge cases to add in route implementations


def test_upload_submission_missing_file(client):
    """Test /upload_submission returns error when file is missing."""
    # Note: Depending on your app error handling, this might raise an exception.
    response = client.post("/upload_submission", data={})
    # We expect a 400 error for missing file
    assert response.status_code == 400


def test_delete_submission_not_found(client, mocker):
    """Test /delete_submission returns 404 when the submission is not found."""
    # Patch the get method to return None.
    # mocker.patch("routes.submission.Submission.query.get", return_value=None)
    mocker.patch(
    "routes.submission.db.session.get",
    return_value=None
)
    response = client.delete("/delete_submission?submission_id=123")
    assert response.status_code == 404
    data = response.get_json()
    assert data["message"] == "No submission found to delete"


# FAILED TEST
def test_upload_assignment_autograder_missing_file(client):
    """Test that /upload_assignment_autograder returns an error message when the file is missing."""
    response = client.post("/upload_assignment_autograder", data={})
    assert response.status_code == 400
    data = response.get_json(silent=True)
    
    if data is not None and "error" in data:
        error_message = data["error"]
    else:
        error_message = response.get_data(as_text=True)
    
    assert "No file part" in error_message


def test_delete_submission_success(client, mocker):
    """Test /delete_submission successfully deletes a submission."""
    fake_submission = mocker.Mock()
    fake_submission.assignment_id = "assgn1"

    # Patch the get method on the api.db.session instead of routes.submission.db.session.get
    fake_get = mocker.patch("api.db.session.get", return_value=fake_submission)
    mock_delete = mocker.patch("routes.submission.db.session.delete")
    mock_commit = mocker.patch("routes.submission.db.session.commit")

    response = client.delete("/delete_submission?submission_id=123")
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Submission successfully deleted"
    
    fake_get.assert_called_once_with(Submission, "123")
    mock_delete.assert_called_once_with(fake_submission)
    mock_commit.assert_called_once()

def test_get_active_submission_missing_params(client):
    response = client.get("/get_active_submission")
    assert response.status_code == 400

    data = response.get_json(silent=True)
    assert data is not None, "Expected a valid JSON response"
    assert data["message"] == "not sufficient details"


# Tests for /get_grade_statistics


def _make_assignment(autograder_points=100):
    assignment = Assignment(
        id=str(uuid.uuid4()),
        name="Test Assignment",
        course_id=str(uuid.uuid4()),
        autograder_points=autograder_points,
    )
    db.session.add(assignment)
    db.session.commit()
    return assignment


def _make_submission(assignment_id, score, active=True, results=None):
    sub = Submission(
        id=str(uuid.uuid4()),
        file_name="solution.py",
        submission_number=1,
        student_id=str(uuid.uuid4()),
        assignment_id=assignment_id,
        student_code_file=b"",
        score=score,
        active=active,
        completed=True,
        results=json.dumps(results).encode("utf-8") if results is not None else None,
    )
    db.session.add(sub)
    db.session.commit()
    return sub


def test_get_grade_statistics_missing_assignment_id(client):
    response = client.get("/get_grade_statistics")
    assert response.status_code == 400
    assert response.get_json()["message"] == "Missing assignment_id"


def test_get_grade_statistics_assignment_not_found(client, mocker):
    mock_query = mocker.patch("routes.submission.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    response = client.get("/get_grade_statistics?assignment_id=missing")
    assert response.status_code == 404
    assert response.get_json()["message"] == "Assignment not found"


def test_get_grade_statistics_forbidden(client, mocker):
    from util.errors import ForbiddenError
    mocker.patch(
        "routes.submission._verify_course_staff",
        side_effect=ForbiddenError("Only course staff or administrators can perform this action"),
    )

    response = client.get("/get_grade_statistics?assignment_id=assgn1")
    assert response.status_code == 403


def test_get_grade_statistics_no_graded_submissions(app, client):
    with app.app_context():
        assignment_id = _make_assignment(autograder_points=100).id

        response = client.get(f"/get_grade_statistics?assignment_id={assignment_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 0
        assert data["mean"] is None
        assert data["median"] is None
        assert data["min"] is None
        assert data["max"] is None
        assert data["stdev"] is None
        assert data["histogram"] == []


def test_get_grade_statistics_ignores_active_but_ungraded(app, client):
    with app.app_context():
        assignment_id = _make_assignment(autograder_points=100).id
        _make_submission(assignment_id, score=None, active=True)

        response = client.get(f"/get_grade_statistics?assignment_id={assignment_id}")
        assert response.status_code == 200
        assert response.get_json()["count"] == 0


def test_get_grade_statistics_ignores_inactive_submissions(app, client):
    with app.app_context():
        assignment_id = _make_assignment(autograder_points=100).id
        _make_submission(assignment_id, score=90, active=True)
        _make_submission(assignment_id, score=10, active=False)

        response = client.get(f"/get_grade_statistics?assignment_id={assignment_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 1
        assert data["mean"] == 90
        assert data["max"] == 90
        assert data["min"] == 90


def test_get_grade_statistics_success_percentage_mode(app, client):
    with app.app_context():
        assignment_id = _make_assignment(autograder_points=100).id
        for score in [50, 60, 70, 85, 95, 100]:
            _make_submission(assignment_id, score=score, active=True)

        response = client.get(f"/get_grade_statistics?assignment_id={assignment_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 6
        assert data["mean"] == pytest.approx(76.67, abs=0.01)
        assert data["median"] == 77.5
        assert data["min"] == 50
        assert data["max"] == 100
        assert data["mode"] == "percentage"

        buckets_by_label = {b["label"]: b["count"] for b in data["histogram"]}
        assert buckets_by_label["50-60%"] == 1
        assert buckets_by_label["60-70%"] == 1
        assert buckets_by_label["70-80%"] == 1
        assert buckets_by_label["80-90%"] == 1
        assert buckets_by_label["90-100%"] == 2
        assert buckets_by_label["0-10%"] == 0


def test_get_grade_statistics_autograder_points_zero(app, client):
    with app.app_context():
        assignment_id = _make_assignment(autograder_points=0).id
        _make_submission(assignment_id, score=5, active=True)
        _make_submission(assignment_id, score=8, active=True)

        response = client.get(f"/get_grade_statistics?assignment_id={assignment_id}")
        assert response.status_code == 200
        assert response.get_json()["mode"] == "raw"


def test_get_grade_statistics_raw_mode_no_max_points(app, client):
    with app.app_context():
        assignment_id = _make_assignment(autograder_points=None).id
        for score in [10, 20, 30]:
            _make_submission(assignment_id, score=score, active=True)

        response = client.get(f"/get_grade_statistics?assignment_id={assignment_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["mode"] == "raw"
        assert data["histogram"][0]["bucket_start"] == 10
        assert data["histogram"][-1]["bucket_end"] == 30


def test_get_grade_statistics_single_submission(app, client):
    with app.app_context():
        assignment_id = _make_assignment(autograder_points=None).id
        _make_submission(assignment_id, score=42, active=True)

        response = client.get(f"/get_grade_statistics?assignment_id={assignment_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 1
        assert data["stdev"] == 0.0
        assert len(data["histogram"]) == 1
        assert data["histogram"][0]["count"] == 1
        assert data["histogram"][0]["bucket_start"] == 42
        assert data["histogram"][0]["bucket_end"] == 42


def test_get_grade_statistics_extra_credit_overflow_bucket(app, client):
    with app.app_context():
        assignment_id = _make_assignment(autograder_points=100).id
        _make_submission(assignment_id, score=110, active=True)

        response = client.get(f"/get_grade_statistics?assignment_id={assignment_id}")
        assert response.status_code == 200
        data = response.get_json()
        buckets_by_label = {b["label"]: b["count"] for b in data["histogram"]}
        assert buckets_by_label[">100%"] == 1
        assert buckets_by_label["90-100%"] == 0


def test_get_grade_statistics_prefers_results_derived_max_over_stale_autograder_points(app, client):
    """Assignment.autograder_points can drift from what the autograder
    actually grades out of (e.g. left at a stale default of 100 while the
    configured test suite only totals 20 points). A submission that aced
    every test should show up as 100%, not get diluted against the stale
    field.
    """
    results = {
        "tests": [
            {"name": "test_1", "score": 10, "max_score": 10, "status": "passed"},
            {"name": "test_2", "score": 10, "max_score": 10, "status": "passed"},
        ]
    }
    with app.app_context():
        assignment_id = _make_assignment(autograder_points=100).id
        _make_submission(assignment_id, score=20, active=True, results=results)

        response = client.get(f"/get_grade_statistics?assignment_id={assignment_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["max_points"] == 20
        buckets_by_label = {b["label"]: b["count"] for b in data["histogram"]}
        assert buckets_by_label["90-100%"] == 1


def test_get_grade_statistics_falls_back_to_autograder_points_when_no_results(app, client):
    """When no submission has parseable results yet (e.g. all still
    processing), fall back to the assignment's configured max points
    rather than reporting a max of 0.
    """
    with app.app_context():
        assignment_id = _make_assignment(autograder_points=50).id
        _make_submission(assignment_id, score=25, active=True, results=None)

        response = client.get(f"/get_grade_statistics?assignment_id={assignment_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["max_points"] == 50
        buckets_by_label = {b["label"]: b["count"] for b in data["histogram"]}
        assert buckets_by_label["50-60%"] == 1

