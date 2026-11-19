from flask import g, session

from api import db
from api.models import Course, Enrollment, User
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
    and 403s, and require_admin() finds no user and 403s. A route that
    only calls require_authenticated() with no follow-up role check
    would not get that safety net.
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


def get_user_global_role(user_id):
    """Returns users.role (admin/instructor/student) lowercased, or None if the user doesn't exist."""
    cache = g.setdefault("_global_role_cache", {})
    if user_id in cache:
        return cache[user_id]

    user = db.session.query(User).filter_by(id=user_id).first()
    role = user.role.lower() if user and user.role else None
    cache[user_id] = role
    return role


def require_admin(message="Admin access required"):
    """401 if not logged in, 403 unless the session user has the global admin role."""
    user_id = require_authenticated()
    if get_user_global_role(user_id) != "admin":
        raise ForbiddenError(message)
    return user_id


def require_self_or_admin(target_user_id, message="You can only access your own account"):
    """Lets a user act on their own account without a DB lookup; anyone else must be an admin."""
    user_id = require_authenticated()
    if str(user_id) == str(target_user_id):
        return user_id
    return require_admin(message)
