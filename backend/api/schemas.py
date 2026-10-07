from api.models import Course, Enrollment, Assignment, Submission, User, TestCaseResult, TestCase, RegradeRequest, AssignmentExtension, CodeDraft
import io

from marshmallow import fields

from api import ma
from ai_feedback.source_extraction import SourceExtractionError, extract_source_from_zip


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
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
        exclude = ("ai_feedback_api_key",)

def submission_code_as_text(raw):
    """Return a stored submission file as displayable text.

    Plain source files are returned as-is. A .zip upload is binary, so it is
    shown as the source files inside it instead of failing to decode.
    """
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        return extract_source_from_zip(io.BytesIO(raw))
    except SourceExtractionError:
        return "[This submission is a binary file and cannot be displayed.]"


class SubmissionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Submission
        include_fk = True

    student_code_file = fields.Method("get_student_code_file")

    def get_student_code_file(self, obj):
        return submission_code_as_text(obj.student_code_file)


class TestCaseSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TestCase
        include_fk = True

class TestCaseResultSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TestCaseResult
        include_fk = True
        include_relationships = True  # Add this if you want to include relationships in the serialized data

class RegradeRequestSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = RegradeRequest
        include_fk = True
        include_relationships = True  # Add this if you want to include relationships in the serialized data

class AssignmentExtensionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AssignmentExtension
        include_fk = True
        include_relationships = True

class CodeDraftSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CodeDraft
        include_fk = True  # Add this if you want to include relationships in the serialized data
