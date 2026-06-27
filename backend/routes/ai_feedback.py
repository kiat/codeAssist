from flask import Blueprint, jsonify, request
from flask_cors import cross_origin

from ai_feedback.settings import (
    serialize_assignment_ai_settings,
    update_assignment_ai_settings,
)
from api import db
from api.models import Assignment
from util.errors import BadRequestError, InternalProcessingError, NotFoundError


ai_feedback = Blueprint("ai_feedback", __name__)

# TODO: add server-side instructor authorization when shared auth middleware is
# available. These routes currently follow the existing assignment route pattern.

@ai_feedback.route("/assignments/<assignment_id>/ai-settings", methods=["GET"])
@cross_origin()
def get_assignment_ai_settings(assignment_id):
    assignment_obj = db.session.query(Assignment).filter_by(id=assignment_id).first()

    if not assignment_obj:
        raise NotFoundError("Assignment not found")

    return jsonify(serialize_assignment_ai_settings(assignment_obj)), 200


@ai_feedback.route("/assignments/<assignment_id>/ai-settings", methods=["PUT"])
@cross_origin()
def update_assignment_ai_settings_route(assignment_id):
    assignment_obj = db.session.query(Assignment).filter_by(id=assignment_id).first()

    if not assignment_obj:
        raise NotFoundError("Assignment not found")

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
