from marshmallow import Schema, fields
from sqlalchemy.dialects.postgresql import DATE, TIMESTAMP, UUID
from sqlalchemy.types import LargeBinary
from api import db

class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    email_address = db.Column(db.String, nullable=False)
    sis_user_id = db.Column(db.String, nullable=False, unique = True)

class Instructor(db.Model):
    __tablename__ = "instructors"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    email_address = db.Column(db.String, nullable=False)
    sis_user_id = db.Column(db.String, nullable=False)

class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    instructor_id = db.Column(UUID(as_uuid=False), db.ForeignKey("instructors.id"), nullable=False)
    sis_course_id = db.Column(db.String, nullable=True)
    semester = db.Column(db.String, nullable=False)
    year = db.Column(db.String, nullable = False)
    entryCode = db.Column(db.String, nullable = False)
    allowEntryCode = db.Column(db.Boolean, default = False)
    description = db.Column(db.String, default = "")


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("students.id"), primary_key=True, nullable=False)
    course_id = db.Column(UUID(as_uuid=False), db.ForeignKey("courses.id"), primary_key = True,  nullable=False)


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
    published_date = db.Column (TIMESTAMP, nullable=True)
    autograder_file = db.Column(LargeBinary, nullable=True)
    


class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    student_id = db.Column(UUID(as_uuid=False), db.ForeignKey("students.id"), nullable=False, index=True)
    assignment_id = db.Column(UUID(as_uuid=False), db.ForeignKey("assignments.id"), nullable=False, index=True)
    student_code_file = db.Column(LargeBinary, nullable=False)
    results = db.Column(LargeBinary, nullable=True)
    score = db.Column(db.Float, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)
    executed_at = db.Column(TIMESTAMP, nullable=True)
    completed = db.Column(db.Boolean, nullable=False)