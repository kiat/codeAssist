from marshmallow import Schema, fields
from sqlalchemy.dialects.postgresql import DATE, TIMESTAMP, UUID
from sqlalchemy.types import LargeBinary
from api import db

class People(db.Model):
    __tablename__ = "people"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    email_address = db.Column(db.String, nullable=False)
    sis_user_id = db.Column(db.String, nullable=False, unique=True)
    role = db.Column(db.String, nullable = False)


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    instructor_id = db.Column(UUID(as_uuid=False), db.ForeignKey("instructors.id"), nullable=False)
    sis_course_id = db.Column(db.String, nullable=True)
    semester = db.Column(db.String, nullable=False)
    year = db.Column(db.String, nullable=False)
    entryCode = db.Column(db.String, nullable=False)
    allowEntryCode = db.Column(db.Boolean, default=False)
    description = db.Column(db.String, default="")

class Enrollment(db.Model):
    __tablename__ = "enrollments"
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("students.id"), primary_key=True, nullable=False)
    course_id = db.Column(UUID(as_uuid=False), db.ForeignKey("courses.id"), primary_key=True, nullable=False)

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

class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    file_name = db.Column(db.String, nullable=False)
    submission_number = db.Column(db.Integer, nullable=False)
    submitted_at = db.Column(TIMESTAMP, nullable=True)
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("students.id"), nullable=False, index=True)
    assignment_id = db.Column(UUID(as_uuid=False), db.ForeignKey("assignments.id"), nullable=False, index=True)
    student_code_file = db.Column(LargeBinary, nullable=False)
    results = db.Column(LargeBinary, nullable=True)
    score = db.Column(db.Float, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=False)
    completed = db.Column(db.Boolean, nullable=False)
    
# Handling multiple submitters for a single submission
class SubmissionSubmitter(db.Model):
    __tablename__ = "submission_submitters"
    submission_id = db.Column(UUID(as_uuid=False), db.ForeignKey("submissions.id"), primary_key=True, nullable=False)
    submitter_id = db.Column(UUID(as_uuid=False), db.ForeignKey("students.id"), primary_key=True, nullable=False)
    
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
