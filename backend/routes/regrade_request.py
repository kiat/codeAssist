import uuid
from flask import Blueprint, request, jsonify
from api import db
from api.models import Assignment, Submission, User, RegradeRequest
from api.schemas import SubmissionSchema, UserSchema
from util.errors import NotFoundError, BadRequestError


regrade_request = Blueprint('regrade_request', __name__)

@regrade_request.route('/send_regrade_request', methods=["POST"])
def send_regrade_request():
    '''
    /send_regrade_request creates a regrade request
    Requires from the frontend a JSON containing:
    @param submission_id         submission
    @param justification     justification for the request
    '''

    request_id = str(uuid.uuid4())
    submission_id = request.json['submission_id']
    justification = request.json['justification']

    request_data = {
        "id": request_id,
        "submission_id": submission_id,
        "justification": justification
    }

    db.session.add(RegradeRequest(**request_data))
    db.session.commit()

    res = db.session.query(RegradeRequest).filter_by(id=request_id)
    res = UserSchema().dump(res, many=True)[0]
    response = jsonify(res)
    return response

@regrade_request.route('/get_regrade_request', methods=["GET"])
def get_regrade_request():
    '''
    /get_regrade_request gets the regrade request associated with a submission_id
    Requires from the frontend a JSON containing:
    @param submission_id    the id of the submission
    '''
    submission_id = request.args.get("submission_id")
    if not submission_id:
        raise BadRequestError("No submission id passed")

    submission = Submission.query.filter_by(id=submission_id).first()
    if not submission:
        raise NotFoundError("No such submission")
    regrade = RegradeRequest.query.filter_by(submission_id=submission_id).first()
    if not regrade :
        raise NotFoundError("No regrade request found")
    response = {
        "submission": SubmissionSchema().dump(submission),
        "justification": regrade.justification,
        "reviewed": regrade.reviewed
    }
    return jsonify(response)

@regrade_request.route('/update_grade', methods=["POST"])
def update_grade():
    '''
    /update_grade updates the grade of a submission
    Requires from the frontend a JSON containing:
    @param submission_id    the id of the submission
    @param new_grade        the new grade to be assigned
    '''
    data = request.json
    submission_id = data.get('submission_id')
    new_grade = data.get('new_grade')

    if not submission_id or new_grade is None:
        raise BadRequestError("Missing submission_id or new_grade")
    submission = Submission.query.filter_by(id=submission_id).first()

    if not submission:
        raise NotFoundError("No such submission found")

    try:
        new_grade = float(new_grade)  # Ensure the grade is a float
    except ValueError:
        raise BadRequestError("Invalid grade value")

    submission.score = new_grade
    db.session.commit()

    return jsonify({"message": "Grade updated successfully"}), 200


@regrade_request.route('/get_student_regrade_requests', methods=["GET"])
def get_student_regrade_requests():
    student_id = request.args.get("student_id")
    course_id = request.args.get("course_id")

    if not student_id:
        raise BadRequestError("Missing student_id")

    if not course_id:
        raise BadRequestError("Missing course_id")

    regrade_requests = db.session.query(RegradeRequest).join(Submission).join(Assignment).filter(
        Submission.student_id == student_id,
        Assignment.course_id == course_id
    ).all()

    result = []
    for req in regrade_requests:
        submission = db.session.query(Submission).filter_by(id=req.submission_id).first()
        assignment = db.session.query(Assignment).filter_by(id=submission.assignment_id).first()
        student = db.session.query(User).filter_by(id=submission.student_id).first()
        result.append({
            "regradeRequestId": req.id,
            "assignmentName": assignment.name,
            "studentName": student.name,
            "justification": req.justification,
            "assignmentId": assignment.id,
            "studentId": student.id,
            "reviewed": req.reviewed
        })

    return jsonify(result), 200

@regrade_request.route('/get_instructor_regrade_requests', methods=["GET"])
def get_instructor_regrade_requests():
    course_id = request.args.get("course_id")
    regrade_requests = db.session.query(RegradeRequest).join(Submission).join(Assignment).filter(Assignment.course_id == course_id)

    result = []
    for req in regrade_requests:
        submission = db.session.query(Submission).filter_by(id=req.submission_id).first()
        assignment = db.session.query(Assignment).filter_by(id=submission.assignment_id).first()
        student = db.session.query(User).filter_by(id=submission.student_id).first()
        result.append({
            "assignmentName": assignment.name,
            "studentName": student.name,
            "justification": req.justification,
            "assignmentId": assignment.id,
            "studentId": student.id,
            "reviewed": req.reviewed
        })

    return jsonify(result), 200

@regrade_request.route('/set_reviewed', methods=['POST', 'OPTIONS'])
def set_reviewed():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200  # Preflight response
    submissionid = request.json["submission_id"]
    entry = db.session.query(RegradeRequest).filter_by(submission_id=submissionid).first()
    
    if entry is None:
        raise NotFoundError(f"No regrade request found for submission_id: {submissionid}")
    entry.reviewed = True
    db.session.commit()

    return jsonify({"message": "Review updated successfully"}), 200

@regrade_request.route('/check_regrade_request', methods=["POST"])
def check_regrade_request():
    submission_id = request.json["submission_id"]
    regrade_request = db.session.query(RegradeRequest).filter_by(submission_id=submission_id).first()
    if not regrade_request:
        return jsonify({"has_request": False}), 200
    return jsonify({"has_request": True}), 200

@regrade_request.route('/delete_regrade_request', methods=["POST"])
def delete_regrade_request():
    submission_id = request.json["submission_id"]
    RegradeRequest.query.filter_by(submission_id=submission_id).delete()
    db.session.commit()
    return jsonify({"message": "Regrade request deleted"}), 200