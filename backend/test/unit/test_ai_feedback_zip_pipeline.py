import json
import uuid
import zipfile
from datetime import datetime, timezone

import pytest

from api import create_app, db
from api.models import Assignment, Course, StudentSubmissionInsight, Submission, User
from ai_feedback.integration import async_get_ai_feedback


@pytest.fixture
def app():
    app = create_app(config_class="config.TestConfig")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def test_async_ai_feedback_extracts_source_from_zip(app, tmp_path, mocker):
    student_id = str(uuid.uuid4())
    instructor_id = str(uuid.uuid4())
    course_id = str(uuid.uuid4())
    assignment_id = str(uuid.uuid4())
    submission_id = str(uuid.uuid4())

    with app.app_context():
        db.session.add(User(
            id=student_id,
            password="pw",
            name="Student",
            email_address="student@example.com",
            sis_user_id="stu-1",
            role="student",
        ))
        db.session.add(User(
            id=instructor_id,
            password="pw",
            name="Instructor",
            email_address="instructor@example.com",
            sis_user_id="inst-1",
            role="instructor",
        ))
        db.session.add(Course(
            id=course_id,
            name="CS",
            instructor_id=instructor_id,
            semester="Fall",
            year="2026",
            entryCode="ziptest",
            default_ai_provider="openai",
            default_ai_model="gpt-4o-mini",
            default_feedback_style="balanced",
            default_ai_temperature=0.5,
        ))
        db.session.add(Assignment(
            id=assignment_id,
            name="Zip Assignment",
            description="Read code from uploaded archives.",
            course_id=course_id,
            ai_feedback_enabled=True,
            use_course_ai_default=True,
        ))
        db.session.add(Submission(
            id=submission_id,
            file_name="submission.zip",
            submission_number=1,
            submitted_at=datetime.now(timezone.utc),
            student_id=student_id,
            assignment_id=assignment_id,
            student_code_file=b"zip bytes",
            results=b"{}",
            score=1,
            execution_time=0.1,
            active=True,
            completed=True,
        ))
        db.session.commit()

        zip_path = tmp_path / "submission.zip"
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("main.py", "print('zip feedback')\n")

        captured = {}

        mocker.patch(
            "ai_feedback.integration.get_provider_credentials",
            return_value=("api-key", object()),
        )

        def fake_get_feedback_by_provider(
            provider,
            api_key,
            client,
            prompt,
            model,
            temperature,
            past_insights,
            vertex_location=None,
        ):
            captured["prompt"] = prompt
            return (
                {
                    "insights": ["Overall Summary: ZIP feedback works."],
                    "annotations": [],
                },
                ["Overall Summary: ZIP feedback works."],
            )

        mocker.patch(
            "ai_feedback.integration.get_feedback_by_provider",
            side_effect=fake_get_feedback_by_provider,
        )

        async_get_ai_feedback(app, submission_id, str(zip_path), '{"score": 1}')

        updated_submission = db.session.get(Submission, submission_id)
        feedback = json.loads(updated_submission.ai_feedback)
        insight_record = StudentSubmissionInsight.query.filter_by(
            submission_id=submission_id
        ).first()
        updated_student = db.session.get(User, student_id)

        assert "File: main.py" in captured["prompt"]
        assert "print('zip feedback')" in captured["prompt"]
        assert feedback["insights"] == ["Overall Summary: ZIP feedback works."]
        assert insight_record.summary == "- Overall Summary: ZIP feedback works."
        assert "ZIP feedback works" in updated_student.coding_insights


def test_async_ai_feedback_logs_internal_error_but_saves_safe_feedback(
    app,
    tmp_path,
    mocker,
    capsys,
):
    student_id = str(uuid.uuid4())
    instructor_id = str(uuid.uuid4())
    course_id = str(uuid.uuid4())
    assignment_id = str(uuid.uuid4())
    submission_id = str(uuid.uuid4())

    with app.app_context():
        db.session.add(User(
            id=student_id,
            password="pw",
            name="Student",
            email_address="student@example.com",
            sis_user_id="stu-1",
            role="student",
        ))
        db.session.add(User(
            id=instructor_id,
            password="pw",
            name="Instructor",
            email_address="instructor@example.com",
            sis_user_id="inst-1",
            role="instructor",
        ))
        db.session.add(Course(
            id=course_id,
            name="CS",
            instructor_id=instructor_id,
            semester="Fall",
            year="2026",
            entryCode="safe-error",
            default_ai_provider="openai",
            default_ai_model="gpt-4o-mini",
            default_feedback_style="balanced",
            default_ai_temperature=0.5,
        ))
        db.session.add(Assignment(
            id=assignment_id,
            name="Safe Error Assignment",
            course_id=course_id,
            ai_feedback_enabled=True,
            use_course_ai_default=True,
        ))
        db.session.add(Submission(
            id=submission_id,
            file_name="submission.py",
            submission_number=1,
            submitted_at=datetime.now(timezone.utc),
            student_id=student_id,
            assignment_id=assignment_id,
            student_code_file=b"print('hello')",
            results=b"{}",
            score=1,
            execution_time=0.1,
            active=True,
            completed=True,
        ))
        db.session.commit()

        source_path = tmp_path / "submission.py"
        source_path.write_text("print('hello')\n", encoding="utf-8")

        mocker.patch(
            "ai_feedback.integration.get_provider_credentials",
            return_value=("api-key", object()),
        )
        mocker.patch(
            "ai_feedback.integration.get_feedback_by_provider",
            side_effect=RuntimeError("provider rejected project test-project"),
        )

        async_get_ai_feedback(app, submission_id, str(source_path), '{"score": 1}')

        output = capsys.readouterr().out
        updated_submission = db.session.get(Submission, submission_id)
        feedback = json.loads(updated_submission.ai_feedback)

        assert "provider rejected project test-project" in output
        assert f"submission {submission_id}" in output
        assert feedback == {
            "error": "AI feedback could not be generated at this time.",
            "insights": ["AI feedback could not be generated at this time."],
            "annotations": [],
        }
        assert "provider rejected project test-project" not in updated_submission.ai_feedback
