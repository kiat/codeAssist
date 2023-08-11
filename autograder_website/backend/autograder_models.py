from autograder_app import db
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.types import LargeBinary

class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    student_code_file = db.Column(LargeBinary, nullable=False)
    results = db.Column(LargeBinary, nullable=True)
    score = db.Column(db.Float, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)
    executed_at = db.Column(TIMESTAMP, nullable=True)