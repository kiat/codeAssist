from marshmallow import Schema, fields
from sqlalchemy.dialects.postgresql import DATE, TIMESTAMP, UUID
from sqlalchemy.types import LargeBinary
from api import db
from dataclasses import dataclass
import docker
import os
import shutil
import logging

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    email_address = db.Column(db.String, nullable=False, unique=True)
    sis_user_id = db.Column(db.String, nullable=False, unique=True)
    role = db.Column(db.String, nullable = False)

    # -- AI Integration -- 
    coding_insights = db.Column(db.String, default="No history.")

class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    instructor_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    sis_course_id = db.Column(db.String, nullable=True)
    semester = db.Column(db.String, nullable=False)
    year = db.Column(db.String, nullable=False)
    entryCode = db.Column(db.String, nullable=False, unique=True)
    allowEntryCode = db.Column(db.Boolean, default=False)
    description = db.Column(db.String, default="")

    # -- AI Integration Settings -- 
    default_ai_provider = db.Column(db.String, default="openai")
    default_ai_model = db.Column(db.String, default="gpt-4o-mini")

    openai_api_key = db.Column(db.String, default="")
    gemini_api_key = db.Column(db.String, default="")
    claude_api_key = db.Column(db.String, default="")
    ollama_base_url = db.Column(db.String, default="")

    default_feedback_style = db.Column(db.String, default="hint-based")
    default_ai_temperature = db.Column(db.Float, default=0.5)

@dataclass
class Enrollment(db.Model):
    __tablename__ = "enrollments"
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    course_id = db.Column(UUID(as_uuid=False), db.ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    role = db.Column(db.String, nullable = False)

class Assignment(db.Model):
    __tablename__ = "assignments"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(UUID(as_uuid=False), db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    due_date = db.Column(TIMESTAMP(timezone=True), nullable=True)
    anonymous_grading = db.Column(db.Boolean, default=False)
    enable_group = db.Column(db.Boolean, default=False)
    group_size = db.Column(db.Integer, nullable=True)
    leaderboard = db.Column(db.Integer, nullable=True)
    late_submission = db.Column(db.Boolean, default=False)
    late_due_date = db.Column(TIMESTAMP(timezone=True), nullable=True)
    manual_grading = db.Column(db.Boolean, default=False)
    autograder_points = db.Column(db.Float, nullable=True)
    published = db.Column(db.Boolean, default=False)
    published_date = db.Column(TIMESTAMP(timezone=True), nullable=True)
    autograder_file = db.Column(LargeBinary, nullable=True)
    container_id = db.Column(db.String)
    autograder_image_name = db.Column(db.String)
    autograder_timeout = db.Column(db.Integer, default=300)

    # -- Submission Method Settings --
    allow_file_upload = db.Column(db.Boolean, default=True)
    enable_code_editor = db.Column(db.Boolean, default=False)

    # -- AI Integration Settings -- 

    ai_feedback_enabled = db.Column(db.Boolean, default=False)
    use_course_ai_default = db.Column(db.Boolean, default=True)
    ai_feedback_provider = db.Column(db.String, nullable=True)
    ai_feedback_model = db.Column(db.String, nullable=True)
    ai_feedback_api_key = db.Column(db.String, default="")
    ai_feedback_prompt = db.Column(db.Text, nullable=True)
    ai_feedback_prompts = db.Column(db.JSON, nullable=True)
    ai_allowed_inputs = db.Column(db.JSON, nullable=True)
    ai_feedback_temperature = db.Column(db.Float, nullable=True)
    ai_feedback_style = db.Column(db.String, nullable=True)
    ai_feedback_max_requests = db.Column(db.Integer, nullable=True)
    ai_feedback_wait_seconds = db.Column(db.Integer, nullable=False, default=0)

def cleanup_assignment_container(container_id, assignment_id=None):
    """Stop and remove the persistent grading container of a deleted assignment.

    Call this from the delete route *after* its transaction has committed, never
    from a mapper-level flush event. Blocking Docker I/O during flush holds the
    transaction and its row locks open across a round trip to the Docker socket,
    which SQLAlchemy warns against and which a hung daemon turns into a stalled
    request. Running it before the commit is worse still: a failed commit rolls
    the rows back, but a destroyed container does not come back.
    """
    if not container_id:
        return
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        container.stop()
        container.remove(force=True)
    except docker.errors.NotFound:
        return
    except Exception:
        logging.getLogger(__name__).warning(
            "Failed to clean up container %s for deleted assignment %s",
            container_id, assignment_id, exc_info=True
        )


def cleanup_assignment_directories(assignment_id):
    """Remove the runs/ and archive/ trees of a deleted assignment.

    Same contract as cleanup_assignment_container: after a successful commit
    only. These trees hold the archived student submissions and results JSON,
    so deleting them ahead of the commit loses data a rollback cannot restore.
    """
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_dir = os.path.join(backend_dir, "routes", "upload_autograder")
    for subtree in ("runs", "archive"):
        shutil.rmtree(os.path.join(base_dir, subtree, str(assignment_id)), ignore_errors=True)

class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    file_name = db.Column(db.String, nullable=False)
    submission_number = db.Column(db.Integer, nullable=False)
    submitted_at = db.Column(TIMESTAMP(timezone=True), nullable=True)
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id = db.Column(UUID(as_uuid=False), db.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_code_file = db.Column(LargeBinary, nullable=False)
    results = db.Column(LargeBinary, nullable=True)
    score = db.Column(db.Float, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=False)
    completed = db.Column(db.Boolean, nullable=False)

    # -- AI Integration Settings -- 
    ai_feedback = db.Column(db.Text, nullable=True)


class StudentSubmissionInsight(db.Model):
    __tablename__ = "student_submission_insights"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id = db.Column(UUID(as_uuid=False), db.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = db.Column(UUID(as_uuid=False), db.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    insights = db.Column(db.JSON, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now())

    student = db.relationship("User", backref=db.backref("submission_insights", lazy="dynamic"))
    assignment = db.relationship("Assignment", backref=db.backref("student_submission_insights", lazy="dynamic"))
    submission = db.relationship("Submission", backref=db.backref("student_submission_insight", uselist=False))
    
# Handling multiple submitters for a single submission
class SubmissionSubmitter(db.Model):
    __tablename__ = "submission_submitters"
    submission_id = db.Column(UUID(as_uuid=False), db.ForeignKey("submissions.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    submitter_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    
class TestCase(db.Model):
    __tablename__ = "test_cases"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    assignment_id = db.Column(UUID(as_uuid=False), db.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    test_case_name = db.Column(db.String, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    input_data = db.Column(db.Text, nullable=False)  

    assignment = db.relationship("Assignment", backref=db.backref("test_cases", lazy="dynamic"))

class TestCaseResult(db.Model):
    __tablename__ = "test_case_results"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    submission_id = db.Column(UUID(as_uuid=False), db.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    test_case_id = db.Column(UUID(as_uuid=False), db.ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    student_output = db.Column(db.Text, nullable=True)
    passed = db.Column(db.Boolean, nullable=True)

    submission = db.relationship("Submission", backref=db.backref("test_case_results", lazy="dynamic"))
    test_case = db.relationship("TestCase", backref="results")

class RegradeRequest(db.Model):
    __tablename__ = "regrade_requests"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    submission_id = db.Column(UUID(as_uuid=False), db.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    justification = db.Column(db.Text, nullable=False)
    reviewed = db.Column(db.Boolean, default=False)

    submission = db.relationship("Submission", backref=db.backref("regrade_requests", lazy="dynamic"))

class AssignmentExtension(db.Model):
    __tablename__ = "assignment_extensions"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    assignment_id = db.Column(UUID(as_uuid=False), db.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    release_date_extension = db.Column(TIMESTAMP(timezone=True), nullable=True)
    due_date_extension = db.Column(TIMESTAMP(timezone=True), nullable=True)
    late_due_date_extension = db.Column(TIMESTAMP(timezone=True), nullable=True)

    assignment = db.relationship("Assignment", backref=db.backref("extensions", lazy="dynamic"))
    student = db.relationship("User", backref=db.backref("extensions", lazy="dynamic"))

class CodeDraft(db.Model):
    __tablename__ = "code_drafts"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id = db.Column(UUID(as_uuid=False), db.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    file_name = db.Column(db.String, nullable=True, default="solution.py")
    version_number = db.Column(db.Integer, nullable=False, default=1)
    saved_at = db.Column(TIMESTAMP(timezone=True), nullable=False)
    auto_saved = db.Column(db.Boolean, nullable=False, default=False)

class AIFeedbackRequest(db.Model):
    __tablename__ = "ai_feedback_requests"
    id = db.Column(db.String, primary_key=True, nullable=False)
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id = db.Column(UUID(as_uuid=False), db.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt_id = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)

    student = db.relationship("User", backref=db.backref("ai_feedback_requests", lazy="dynamic"))
    assignment = db.relationship("Assignment", backref=db.backref("ai_feedback_requests", lazy="dynamic"))


class AIChatMessage(db.Model):
    __tablename__ = "ai_chat_messages"
    id = db.Column(db.String, primary_key=True, nullable=False)
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id = db.Column(UUID(as_uuid=False), db.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    role = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)
    prompt_id = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)

    student = db.relationship("User", backref=db.backref("ai_chat_messages", lazy="dynamic"))
    assignment = db.relationship("Assignment", backref=db.backref("ai_chat_messages", lazy="dynamic"))


class AdminEmail(db.Model):
    __tablename__ = 'admin_emails'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return f"<AdminEmail {self.email}>"   
