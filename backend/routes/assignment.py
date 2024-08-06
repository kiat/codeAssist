import uuid
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from api import db
from api.models import Assignment, Submission
from api.schemas import AssignmentSchema, SubmissionSchema

assignment = Blueprint('assignment', __name__)

@assignment.route('/update_assignment', methods=["POST", "GET"])
@cross_origin()
def update_assignment():
    # TODO this method name does not match the extension
    '''
    /update_assignment updates an assignment in the database
    Requires from the frontend a JSON containing:
    @param assignment_id    the id of the assignment
    '''
    new_data = request.json
    assignment_id = request.json["assignment_id"]

    del new_data["assignment_id"]

    new_assignment_name = new_data.get("name")
    course_id = new_data.get("course_id")

    existing_assignment = db.session.query(Assignment).filter(
        Assignment.course_id == course_id,
        Assignment.name == new_assignment_name,
        Assignment.id != assignment_id
    ).first()

    if existing_assignment:
        return jsonify({"message": "An assignment with this name already exists"}), 400

    assignment = db.session.query(Assignment).filter_by(id=assignment_id).update(new_data)

    if not assignment:
        return jsonify({"message": "Assignment not found"}), 404

    db.session.commit()

    return jsonify({"message": "Success"}), 200

@assignment.route('/get_assignment', methods=["GET"])
@cross_origin()
def get_assignment():
    '''
    /get_assignment gets the assignment from the database
    Requires from the frontend a JSON containing:
    @param assignment_id    the id of the assignment
    '''
    assignment_id = request.args.get("assignment_id")

    assignment = db.session.query(Assignment).filter_by(id=assignment_id)
    assignment = AssignmentSchema().dump(assignment, many=True)[0]

    return jsonify(assignment)

@assignment.route('/create_assignment', methods=["POST", "GET"])
@cross_origin()
def create_assignment():
    '''
    /create_assignment creates an assignment and generates an assignment
    id in the database
    '''
    assignment_data = request.json
    # Check for duplicate name
    assignment_name = assignment_data.get("name")
    course_id = assignment_data.get("course_id")
    course_assignments = db.session.query(Assignment).filter_by(course_id=course_id).all()
    for a in course_assignments:
        if a.name == assignment_name:
            return jsonify({"message": "An assignment with this name already exists"}), 400
    assignment_id = str(uuid.uuid4())
    assignment_data["id"] = assignment_id
    valid_assignment_data = {k: v for k,v in assignment_data.items() if v is not None}
    db.session.add(Assignment(**valid_assignment_data))
    db.session.commit()
    newAssignment = db.session.query(Assignment).filter_by(id=assignment_id)
    newAssignment = AssignmentSchema().dump(newAssignment, many=True)[0]
    return jsonify(newAssignment)

@assignment.route('/delete_assignment', methods=["DELETE"])
@cross_origin()
def delete_assignment():
    assignment_id = request.args.get("assignment_id")

    # Check if there are any submissions for this assignment
    related_submissions = db.session.query(Submission).filter_by(assignment_id=assignment_id).all()
    if related_submissions:
        for submission in related_submissions:
            db.session.delete(submission)
        db.session.commit()

    # actually delete assignment
    assignment_to_delete = db.session.query(Assignment).get(assignment_id)
    if assignment_to_delete:
        db.session.delete(assignment_to_delete)
        db.session.commit()
        return jsonify("Assignment deleted successfully"), 200
    else:
        return jsonify("Assignment not found"), 404

@assignment.route('/delete_submissions', methods=["DELETE"])
@cross_origin()
def delete_submissions():
    assignment_id = request.args.get("assignment_id")

    # Check if there are any submissions for this assignment
    related_submissions = db.session.query(Submission).filter_by(assignment_id=assignment_id).all()
    if related_submissions:
        for submission in related_submissions:
            db.session.delete(submission)
        db.session.commit()

    # actually delete assignment
    related_submissions = db.session.query(Submission).filter_by(assignment_id=assignment_id).all()
    if not related_submissions:
        return jsonify("Submissions deleted successfully"), 200
    else:
        return jsonify("Submissions not deleted"), 404
