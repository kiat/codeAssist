import uuid
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from api import db
from api.models import Assignment, Submission, User, RegradeRequest
from api.schemas import SubmissionSchema, UserSchema
# import asyncio
# from openai import AsyncOpenAI


regrade_requests = Blueprint('regrade_requests', __name__)

@regrade_requests.route('/send_regrade_request', methods=["POST"])
@cross_origin()
def send_regrade_request():
    '''
    /send_regrade_request creates a regrade request
    Requires from the frontend a JSON containing:
    @param submission_id         submission
    @param       for the request
    '''

    request_id = str(uuid.uuid4())
    submission_id = request.json['submission_id']
     = request.json['']

    request_data = {
        "id": request_id,
        "submission_id": submission_id,
        "": 
    }

    db.session.add(RegradeRequest(**request_data))
    db.session.commit()

    res = db.session.query(RegradeRequest).filter_by(id=request_id)
    res = UserSchema().dump(res, many=True)[0]
    response = jsonify(res)
    return response

@regrade_requests.route('/get_regrade_request', methods=["GET"])
@cross_origin()
def get_regrade_request():
    '''
    /get_regrade_request gets the regrade request associated with a submission_id
    Requires from the frontend a JSON containing:
    @param submission_id    the id of the submission
    '''
    submission_id = request.args.get("submission_id")
    if not submission_id:
        return jsonify({"message": "no submission id passed"})
    
    submission = Submission.query.filter_by(id=submission_id)
    if not submission:
        return jsonify({"message": "no such submission"})
    regrade = RegradeRequest.query.filter_by(submission_id=submission_id).first()
    if not regrade :
        return jsonify({"message": "No regrade request found"})
    response = {
        "submission": SubmissionSchema().dump(submission),
        "": regrade.,
        "reviewed": regrade.reviewed
    }
    return jsonify(response)

@regrade_requests.route('/update_grade', methods=["POST"])
@cross_origin()
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
        return jsonify({"message": "Missing submission_id or new_grade"}), 400

    submission = Submission.query.filter_by(id=submission_id).first()

    if not submission:
        return jsonify({"message": "No such submission found"}), 404

    try:
        new_grade = float(new_grade)  # Ensure the grade is a float
    except ValueError:
        return jsonify({"message": "Invalid grade value"}), 400

    submission.score = new_grade
    db.session.commit()

    return jsonify({"message": "Grade updated successfully"}), 200


@regrade_requests.route('/get_student_regrade_requests', methods=["GET"])
@cross_origin()
def get_student_regrade_requests():
    student_id = request.args.get("student_id")
    course_id = request.args.get("course_id")

    if not student_id:
        return jsonify({"message": "Missing student_id"}), 400
    
    if not course_id:
        return jsonify({"message": "Missing course_id"}), 400

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
            "": req.,
            "assignmentId": assignment.id,
            "studentId": student.id,
            "reviewed": req.reviewed
        })

    return jsonify(result), 200

@regrade_requests.route('/get_instructor_regrade_requests', methods=["GET"])
@cross_origin()
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
            "": req.,
            "assignmentId": assignment.id,
            "studentId": student.id,
            "reviewed": req.reviewed
        })

    return jsonify(result), 200

@regrade_requests.route('/set_reviewed', methods=['POST'])
@cross_origin()
def set_reviewed():
    submissionid = request.json["submission_id"]
    entry = db.session.query(RegradeRequest).filter_by(submission_id=submissionid).first()
    entry.reviewed = True
    db.session.commit()

    return jsonify({"message": "Review updated successfully"}), 200

@regrade_requests.route('/check_regrade_request', methods=["POST"])
@cross_origin()
def check_regrade_request():
    submission_id = request.json["submission_id"]
    regrade_request = db.session.query(RegradeRequest).filter_by(submission_id=submission_id).first()
    if not regrade_request:
        return jsonify({"has_request": False}), 200
    return jsonify({"has_request": True}), 200

@regrade_requests.route('/delete_regrade_request', methods=["POST"])
@cross_origin()
def delete_regrade_request():
    submission_id = request.json["submission_id"]
    RegradeRequest.query.filter_by(submission_id=submission_id).delete()
    db.session.commit()
    return jsonify({"message": "Regrade request deleted"}), 200