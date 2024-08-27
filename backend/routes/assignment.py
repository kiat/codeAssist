import uuid
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from api import db
from api.models import Assignment, Submission, RegradeRequest, Course, Enrollment
from api.schemas import AssignmentSchema, SubmissionSchema, CourseSchema, EnrollmentSchema

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
    assignment_id = request.json["assignment_id"]

    data = request.json
    del data["assignment_id"]

    assignment = db.session.query(Assignment).filter_by(id=assignment_id).update(data)
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

    course_assignment = db.session.query(Assignment).filter_by(course_id=course_id, name=assignment_name).one_or_none()
    if course_assignment != None:
        return jsonify({"error": "An assignment with this name already exists in this course"}), 404

    assignment_id = str(uuid.uuid4())
    assignment_data["id"] = assignment_id
    # not creating a container yet
    assignment_data["container_id"] = None
    valid_assignment_data = {k: v for k,v in assignment_data.items() if v is not None}

    db.session.add(Assignment(**valid_assignment_data))
    db.session.commit()

    newAssignment = db.session.query(Assignment).filter_by(id=assignment_id)
    newAssignment = AssignmentSchema().dump(newAssignment, many=True)[0]

    return jsonify(newAssignment)

@assignment.route('/duplicate_assignment', methods=["POST", "GET"])
@cross_origin()
def duplicate_assignment():
    '''
    /duplicate_assignment duplicates an existing assignment with a new name
    '''
    assignment_data = request.json

    old_assignment_ID = assignment_data.get("oldAssignmentId")
    new_name = assignment_data.get("newAssignmentTitle")

    # Check old_assignment
    old_assignment = db.session.query(Assignment).filter_by(id=old_assignment_ID).one_or_none()
    if old_assignment is None:
        return jsonify({"error": "Old assignment not found"}), 404
    
    # Check for duplicate name
    course_assignment = db.session.query(Assignment).filter_by(course_id=old_assignment.course_id, name=new_name).one_or_none()
    if course_assignment != None:
        return jsonify({"error": "An assignment with this name already exists in this course"}), 404
    
    # Create new assignment
    new_assignment_id = str(uuid.uuid4())

    old_assignment_data = AssignmentSchema().dump(old_assignment)
    old_assignment_data['id'] = new_assignment_id
    old_assignment_data['name'] = new_name

    new_assignment = Assignment(**old_assignment_data)

    db.session.add(new_assignment)
    db.session.commit()

    new_assignment_data = AssignmentSchema().dump(new_assignment)

    return jsonify(new_assignment_data)

@assignment.route('/delete_assignment', methods=["DELETE"])
@cross_origin()
def delete_assignment():
    assignment_id = request.args.get("assignment_id")

    # Check if there are any submissions for this assignment
    related_submissions = db.session.query(Submission).filter_by(assignment_id=assignment_id).all()
    if related_submissions:
        for submission in related_submissions:
            related_requests = db.session.query(RegradeRequest).filter_by(submission_id = submission.id)
            if related_requests:
                for req in related_requests :
                    db.session.delete(req)
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