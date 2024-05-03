from api.models import Student, Course, Enrollment, Assignment, Submission, Instructor, TestCaseResult, TestCase
from api import ma


class StudentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Student
        include_fk = True

class InstructorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Instructor
        include_fk = True

class CourseSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Course
        include_fk = True

class EnrollmentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Enrollment
        include_fk = True

class AssignmentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Assignment
        include_fk = True

class SubmissionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Submission
        include_fk = True


class TestCaseSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TestCase
        include_fk = True

class TestCaseResultSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TestCaseResult
        include_fk = True
        include_relationships = True  # Add this if you want to include relationships in the serialized data