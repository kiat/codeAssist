from marshmallow import Schema, fields
from sqlalchemy.dialects.postgresql import DATE
from sqlalchemy.types import LargeBinary
from api import db

class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.UUID, primary_key=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    email_address = db.Column(db.String, nullable=False)
    sis_user_id = db.Column(db.String, nullable=True)


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.UUID, primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    sis_course_id = db.Column(db.String, nullable=True)


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    student_id = db.Column(db.UUID, db.ForeignKey("students.id"), primary_key=True, nullable=False)
    course_id = db.Column(db.UUID, db.ForeignKey("courses.id"), primary_key=True, nullable=False)


class Assignment(db.Model):
    __tablename__ = "assignments"
    id = db.Column(db.UUID, primary_key=True, nullable=False)
    name = db.Column(db.String, primary_key=True, nullable=False)
    course_id = db.Column(db.UUID, db.ForeignKey("courses.id"), nullable=False)
    autograder_file = db.Column(LargeBinary, nullable=False)

class Submission(db.Model):
    __tablename__ = "submissions"
    student_id = db.Column(db.UUID, db.ForeignKey("students.id"), nullable=False)
    assignment_id = db.Column(db.UUID, db.ForeignKey("assignemnts.id"), nullable=False)
    student_code_file = db.Column(LargeBinary, nullable=False)
    results = db.Column(LargeBinary, nullable=True)
    score = db.Column(db.Float, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)
    executed_at = db.Column(DATE, nullable=True)
    completed = db.Column(db.Boolean, nullable=False)