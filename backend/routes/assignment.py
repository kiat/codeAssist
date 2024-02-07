import uuid
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from api import db
from api.models import Assignment
from api.schemas import AssignmentSchema

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
    assignment_id = str(uuid.uuid4())
    assignment_data["id"] = assignment_id
    valid_assignment_data = {k: v for k,v in assignment_data.items() if v is not None}

    db.session.add(Assignment(**valid_assignment_data))
    db.session.commit()

    newAssignment = db.session.query(Assignment).filter_by(id=assignment_id)
    newAssignment = AssignmentSchema().dump(newAssignment, many=True)[0]

    return jsonify(newAssignment)

@assignment.route('/delete_assignment', methods = ["DELETE", "OPTIONS"])
@cross_origin()
def delete_assignment():
    if request.method == "OPTIONS":
        return "", 200
    if request.method == "DELETE":
        assignment_id = request.args.get("assignment_id")
        assignment_to_delete = db.session.get(Assignment, assignment_id)
        db.session.delete(assignment_to_delete)
        db.session.commit()

    return jsonify("Assignment deleted successfully")