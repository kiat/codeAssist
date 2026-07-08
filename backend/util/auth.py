from api import db
from api.models import Enrollment


def get_user_course_role(user_id, course_id):
    enrollment = db.session.query(Enrollment).filter_by(
        student_id=user_id, course_id=course_id
    ).first()
    return enrollment.role.lower() if enrollment else None
