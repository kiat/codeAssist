from flask import session

from api import db
from api.models import Enrollment
from util.errors import ForbiddenError, UnauthorizedError


def get_user_course_role(user_id, course_id):
    enrollment = db.session.query(Enrollment).filter_by(
        student_id=user_id, course_id=course_id
    ).first()
    return enrollment.role.lower() if enrollment else None


def require_authenticated():
    user_id = session.get("user_id")
    if not user_id:
        raise UnauthorizedError("Not authenticated")
    return user_id


def require_course_role(course_id, allowed_roles, message):
    user_id = require_authenticated()

    role = get_user_course_role(user_id, course_id)
    if role not in allowed_roles:
        raise ForbiddenError(message)

    return user_id, role
