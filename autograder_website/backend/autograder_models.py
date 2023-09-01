from autograder_app import db, ma
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.types import LargeBinary
from dataclasses import dataclass
from datetime import datetime

class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    student_code_file = db.Column(LargeBinary, nullable=False)
    results = db.Column(LargeBinary, nullable=True)
    score = db.Column(db.Float, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)
    executed_at = db.Column(TIMESTAMP, nullable=True)

class SubmissionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Submission
        include_fk = True

@dataclass
class Message(db.Model):
    __tablename__ = "messages"
    timestamp:datetime = db.Column(TIMESTAMP, nullable=False, primary_key=True)
    message:str = db.Column(db.String, nullable=False)
    
class MessageSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Message
        include_fk = True