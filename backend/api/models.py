from marshmallow import Schema, fields
from sqlalchemy.dialects.postgresql import DATE, TIMESTAMP, UUID
from sqlalchemy.types import LargeBinary
from api import db
from dataclasses import dataclass
class User(db.Model):
    __tablename__ = "user"
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
    instructor_id = db.Column(UUID(as_uuid=False), db.ForeignKey("user.id"), nullable=False)
    sis_course_id = db.Column(db.String, nullable=True)
    semester = db.Column(db.String, nullable=False)
    year = db.Column(db.String, nullable=False)
    entryCode = db.Column(db.String, nullable=False, unique=True)
    allowEntryCode = db.Column(db.Boolean, default=False)
    description = db.Column(db.String, default="")

    # -- AI Integration Settings -- 
    openai_api_key = db.Column(db.String, default="")

@dataclass
class Enrollment(db.Model):
    __tablename__ = "enrollments"
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("user.id"), primary_key=True, nullable=False)
    course_id = db.Column(UUID(as_uuid=False), db.ForeignKey("courses.id"), primary_key=True, nullable=False)
    role = db.Column(db.String, nullable = False)

class Assignment(db.Model):
    __tablename__ = "assignments"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    course_id = db.Column(UUID(as_uuid=False), db.ForeignKey("courses.id"), nullable=False)
    due_date = db.Column(TIMESTAMP, nullable=True)
    anonymous_grading = db.Column(db.Boolean, default=False)
    enable_group = db.Column(db.Boolean, default=False)
    group_size = db.Column(db.Integer, nullable=True)
    leaderboard = db.Column(db.Integer, nullable=True)
    late_submission = db.Column(db.Boolean, default=False)
    late_due_date = db.Column(TIMESTAMP, nullable=True)
    manual_grading = db.Column(db.Boolean, default=False)
    autograder_points = db.Column(db.Float, nullable=True)
    published = db.Column(db.Boolean, default=False)
    published_date = db.Column(TIMESTAMP, nullable=True)
    autograder_file = db.Column(LargeBinary, nullable=True)
    container_id = db.Column(db.String)
    autograder_timeout = db.Column(db.Integer, default=300)

    # -- AI Integration Settings -- 
    ai_feedback_enabled = db.Column(db.Boolean, default=False)
    ai_feedback_prompt = db.Column(db.Text, nullable=True)
    ai_feedback_model = db.Column(db.Text, nullable=True)
    ai_feedback_temperature = db.Column(db.Float, nullable=True)

class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    file_name = db.Column(db.String, nullable=False)
    submission_number = db.Column(db.Integer, nullable=False)
    submitted_at = db.Column(TIMESTAMP, nullable=True)
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("user.id"), nullable=False, index=True)
    assignment_id = db.Column(UUID(as_uuid=False), db.ForeignKey("assignments.id"), nullable=False, index=True)
    student_code_file = db.Column(LargeBinary, nullable=False)
    results = db.Column(LargeBinary, nullable=True)
    score = db.Column(db.Float, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=False)
    completed = db.Column(db.Boolean, nullable=False)

    # -- AI Integration Settings -- 
    ai_feedback = db.Column(db.Text, nullable=True)
    
# Handling multiple submitters for a single submission
class SubmissionSubmitter(db.Model):
    __tablename__ = "submission_submitters"
    submission_id = db.Column(UUID(as_uuid=False), db.ForeignKey("submissions.id"), primary_key=True, nullable=False)
    submitter_id = db.Column(UUID(as_uuid=False), db.ForeignKey("user.id"), primary_key=True, nullable=False)
    
class TestCase(db.Model):
    __tablename__ = "test_cases"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    assignment_id = db.Column(UUID(as_uuid=False), db.ForeignKey("assignments.id"), nullable=False)
    test_case_name = db.Column(db.String, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    input_data = db.Column(db.Text, nullable=False)  

    assignment = db.relationship("Assignment", backref=db.backref("test_cases", lazy="dynamic"))

class TestCaseResult(db.Model):
    __tablename__ = "test_case_results"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    submission_id = db.Column(UUID(as_uuid=False), db.ForeignKey("submissions.id"), nullable=False)
    test_case_id = db.Column(UUID(as_uuid=False), db.ForeignKey("test_cases.id"), nullable=False)
    student_output = db.Column(db.Text, nullable=True)
    passed = db.Column(db.Boolean, nullable=True)

    submission = db.relationship("Submission", backref=db.backref("test_case_results", lazy="dynamic"))
    test_case = db.relationship("TestCase", backref="results")

class RegradeRequest(db.Model):
    __tablename__ = "regrade_requests"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    submission_id = db.Column(UUID(as_uuid=False), db.ForeignKey("submissions.id"), nullable=False)
    justification = db.Column(db.Text, nullable=False)
    reviewed = db.Column(db.Boolean, default=False)

    submission = db.relationship("Submission", backref=db.backref("regrade_requests", lazy="dynamic"))

class AssignmentExtension(db.Model):
    __tablename__ = "assignment_extensions"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    assignment_id = db.Column(UUID(as_uuid=False), db.ForeignKey("assignments.id"), nullable=False)
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("user.id"), nullable=False)
    release_date_extension = db.Column(TIMESTAMP, nullable=True)
    due_date_extension = db.Column(TIMESTAMP, nullable=True)
    late_due_date_extension = db.Column(TIMESTAMP, nullable=True)

    assignment = db.relationship("Assignment", backref=db.backref("extensions", lazy="dynamic"))
    student = db.relationship("User", backref=db.backref("extensions", lazy="dynamic"))

class AdminEmail(db.Model):
    __tablename__ = 'admin_emails'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return f"<AdminEmail {self.email}>"   

