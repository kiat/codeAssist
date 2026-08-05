import uuid
from datetime import datetime, timezone

import pytest

from api import create_app, db
from api.models import Assignment, Course, StudentSubmissionInsight, Submission, User
from ai_feedback.memory import (
    get_recent_submission_history_text,
    record_submission_insight,
)


@pytest.fixture
def app():
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def _seed_submission_history_records():
    student_id = str(uuid.uuid4())
    instructor_id = str(uuid.uuid4())
    course_id = str(uuid.uuid4())
    assignment_id = str(uuid.uuid4())
    first_submission_id = str(uuid.uuid4())
    second_submission_id = str(uuid.uuid4())

    db.session.add(User(
        id=student_id,
        password="pw",
        name="Student",
        email_address="student-memory@example.com",
        sis_user_id="stu-memory",
        role="student",
    ))
    db.session.add(User(
        id=instructor_id,
        password="pw",
        name="Instructor",
        email_address="instructor-memory@example.com",
        sis_user_id="inst-memory",
        role="instructor",
    ))
    db.session.add(Course(
        id=course_id,
        name="CS",
        instructor_id=instructor_id,
        semester="Fall",
        year="2026",
        entryCode="memory",
    ))
    db.session.add(Assignment(
        id=assignment_id,
        name="Loops",
        course_id=course_id,
    ))

    first_submission = Submission(
        id=first_submission_id,
        file_name="first.py",
        submission_number=1,
        submitted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        student_id=student_id,
        assignment_id=assignment_id,
        student_code_file=b"print('first')",
        completed=True,
    )
    second_submission = Submission(
        id=second_submission_id,
        file_name="second.py",
        submission_number=2,
        submitted_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        student_id=student_id,
        assignment_id=assignment_id,
        student_code_file=b"print('second')",
        completed=True,
    )
    db.session.add_all([first_submission, second_submission])
    db.session.commit()

    return student_id, assignment_id, first_submission, second_submission


def test_records_and_renders_multiple_submission_insights(app):
    with app.app_context():
        student_id, assignment_id, first_submission, second_submission = (
            _seed_submission_history_records()
        )

        first_record = record_submission_insight(
            first_submission,
            ["Missed the loop boundary on the first attempt."],
        )
        first_record.created_at = datetime(2026, 1, 3, tzinfo=timezone.utc)
        second_record = record_submission_insight(
            second_submission,
            ["Improved loop boundary handling in the next submission."],
        )
        second_record.created_at = datetime(2026, 1, 4, tzinfo=timezone.utc)
        db.session.commit()

        history = get_recent_submission_history_text(student_id, assignment_id)

        assert "Missed the loop boundary" in history
        assert "Improved loop boundary" in history
        assert history.index("Missed the loop boundary") < history.index("Improved loop boundary")


def test_record_submission_insight_updates_same_submission(app):
    with app.app_context():
        _, _, first_submission, _ = _seed_submission_history_records()

        record_submission_insight(first_submission, ["Original insight"])
        db.session.commit()

        record_submission_insight(first_submission, ["Updated insight"])
        db.session.commit()

        records = StudentSubmissionInsight.query.filter_by(
            submission_id=first_submission.id
        ).all()

        assert len(records) == 1
        assert "Updated insight" in records[0].summary
        assert "Original insight" not in records[0].summary
