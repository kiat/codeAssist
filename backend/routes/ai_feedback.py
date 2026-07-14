from flask import Blueprint, jsonify, request

from ai_feedback.settings import (
    serialize_assignment_ai_settings,
    update_assignment_ai_settings,
)
from api import db
from api.models import Assignment, Course, Enrollment
from util.errors import (
    BadRequestError,
    ForbiddenError,
    InternalProcessingError,
    NotFoundError,
)


ai_feedback = Blueprint("ai_feedback", __name__)


def _get_requester_id():
    requester_id = request.args.get("requester_id")

    if not requester_id and request.is_json:
        requester_id = (request.json or {}).get("requester_id")

    if not requester_id:
        raise ForbiddenError("Missing requester_id for AI settings authorization")

    return requester_id


def _require_instructor_or_ta_for_assignment(assignment_obj):
    requester_id = _get_requester_id()

    course_obj = db.session.query(Course).filter_by(id=assignment_obj.course_id).first()
    if not course_obj:
        raise NotFoundError("Course not found")

    if str(course_obj.instructor_id) == str(requester_id):
        return

    enrollment = (
        db.session.query(Enrollment)
        .filter_by(course_id=assignment_obj.course_id, student_id=requester_id)
        .first()
    )

    if enrollment and str(enrollment.role).lower() in {"instructor", "ta"}:
        return

    raise ForbiddenError("Only instructors or TAs can access assignment AI settings")


@ai_feedback.route("/assignments/<assignment_id>/ai-settings", methods=["GET"])
def get_assignment_ai_settings(assignment_id):
    assignment_obj = db.session.query(Assignment).filter_by(id=assignment_id).first()

    if not assignment_obj:
        raise NotFoundError("Assignment not found")

    _require_instructor_or_ta_for_assignment(assignment_obj)

    return jsonify(serialize_assignment_ai_settings(assignment_obj)), 200


@ai_feedback.route("/assignments/<assignment_id>/ai-settings", methods=["PUT"])
def update_assignment_ai_settings_route(assignment_id):
    assignment_obj = db.session.query(Assignment).filter_by(id=assignment_id).first()

    if not assignment_obj:
        raise NotFoundError("Assignment not found")

    _require_instructor_or_ta_for_assignment(assignment_obj)

    try:
        update_assignment_ai_settings(assignment_obj, request.json or {})
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        raise BadRequestError(str(e))
    except Exception:
        db.session.rollback()
        raise InternalProcessingError("Failed to update assignment AI settings")

    return jsonify(serialize_assignment_ai_settings(assignment_obj)), 200
