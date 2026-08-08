from flask import Blueprint, jsonify, request

from ai_feedback.settings import (
    get_enabled_feedback_prompt,
    normalize_feedback_prompts,
    serialize_assignment_ai_settings,
    update_assignment_ai_settings,
)
from api import db
from api.models import Assignment
from util.auth import require_course_role
from util.errors import (
    BadRequestError,
    InternalProcessingError,
    NotFoundError,
)


ai_feedback = Blueprint("ai_feedback", __name__)


@ai_feedback.route("/assignments/<assignment_id>/ai-settings", methods=["GET"])
def get_assignment_ai_settings(assignment_id):
    assignment_obj = db.session.query(Assignment).filter_by(id=assignment_id).first()

    if not assignment_obj:
        raise NotFoundError("Assignment not found")

    require_course_role(
        assignment_obj.course_id, {"instructor", "ta"}, "Only instructors or TAs can access assignment AI settings"
    )

    return jsonify(serialize_assignment_ai_settings(assignment_obj)), 200


@ai_feedback.route("/assignments/<assignment_id>/prompts", methods=["GET"])
def get_assignment_prompts(assignment_id):
    """Return the enabled AI feedback prompts for a student.

    The student must be enrolled in the assignment's course.
    Returns { ai_feedback_enabled, ai_feedback_prompts }.
    """
    assignment_obj = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment_obj:
        raise NotFoundError("Assignment not found")

    require_course_role(
        assignment_obj.course_id, {"student", "ta", "instructor"}, "You are not enrolled in this course"
    )

    prompts = normalize_feedback_prompts(
        getattr(assignment_obj, "ai_feedback_prompts", None),
        legacy_prompt=getattr(assignment_obj, "ai_feedback_prompt", None),
    )

    enabled_prompts = [p for p in prompts if p.get("enabled")]

    return jsonify({
        "ai_feedback_enabled": bool(getattr(assignment_obj, "ai_feedback_enabled", False)),
        "ai_feedback_prompts": enabled_prompts,
    }), 200


@ai_feedback.route("/assignments/<assignment_id>/ai-settings", methods=["PUT"])
def update_assignment_ai_settings_route(assignment_id):
    assignment_obj = db.session.query(Assignment).filter_by(id=assignment_id).first()

    if not assignment_obj:
        raise NotFoundError("Assignment not found")

    require_course_role(
        assignment_obj.course_id, {"instructor", "ta"}, "Only instructors or TAs can access assignment AI settings"
    )

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
