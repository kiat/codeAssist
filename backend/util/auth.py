from flask import g, session

from api import db
from api.models import Course, Enrollment
from util.errors import ForbiddenError, NotFoundError, UnauthorizedError


def get_user_course_role(user_id, course_id):
    """Returns the caller's role in course_id, or None for both "course doesn't exist" and "not enrolled" (kept indistinguishable so callers can't enumerate valid course IDs via the error)."""
    cache = g.setdefault("_course_role_cache", {})
    cache_key = (user_id, course_id)
    if cache_key in cache:
        return cache[cache_key]

    enrollment = db.session.query(Enrollment).filter_by(
        student_id=user_id, course_id=course_id
    ).first()
    role = enrollment.role.lower() if enrollment and enrollment.role else None
    cache[cache_key] = role
    return role


def require_authenticated():
    """Returns the session user_id without checking the user still exists.

    Trusts the session rather than paying a DB round trip on every call.
    A session for a deleted user is nearly always caught downstream
    anyway: cascade-delete removes the user's enrollments with them, so
    any require_course_role() call for that user_id finds no enrollment
    and 403s. A route that only calls require_authenticated() with no
    follow-up role check would not get that safety net; none currently
    do.
    """
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
