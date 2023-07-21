import uuid
import docker_client
import json
import sys
from werkzeug.utils import secure_filename
from functools import reduce
from flask import Blueprint, request, jsonify, flash
from flask_cors import cross_origin
from api import db
from api.models import Assignment, Submission
from api.schemas import AssignmentSchema, SubmissionSchema

submission = Blueprint('submission', __name__)

ALLOWED_EXTENSIONS = {'py','zip'}

def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@submission.route('/get_submissions', methods=["GET"])
@cross_origin()
def get_submission():
    '''
    /get_submissions gets all submissions by a student for an assignment
    Requires from the frontend a JSON containing:
    @param student_id       the id of a student
    @param assignment_id    the id of an assignment
    '''
    student_id = request.args.get("student_id")
    assignment_id = request.args.get("assignment_id")

    submissions = db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id)
    submissions = SubmissionSchema().dump(submissions, many=True)

    return jsonify(submissions)
    
@submission.route('/upload_submission', methods=["POST", "GET"])
@cross_origin()
def upload_file():
    # TODO the method name does not match the extension
    '''
    /upload_submission uploads a submission by a student for an assignment into
    the database
    Requires from the frontend a JSON containing:
    @param assignment       assignment #TODO whoever knows better, document
    @param student_id       the id of a student
    @param assignment_id    the id of an assignment
    '''
    print(request.files)
    print(request.form)
    if "file" not in request.files:
        flash("No file part")
        return "no file\n"
    file = request.files["file"]
    assignment = request.form["assignment"].lower()
    student_id = request.form["student_id"]
    assignment_id = request.form["assignment_id"]

    if file.filename == "":
        flash("No selected file")
        return "no selected file"
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        new_uuid = str(uuid.uuid4())

        submission_data = {
            "id": new_uuid,
            "student_id": student_id,
            "assignment_id": assignment_id,
            "student_code_file": file.read(),
            "completed": False
        }

        file.seek(0)

        db.session.add(Submission(**submission_data))
        db.session.commit()
       
        logs, results = docker_client.run_container(assignment, file, filename, new_uuid)

        submission_data["results"] = results.encode('utf8')
        submission_data["completed"] = True

        print(results, file=sys.stderr)
        tests = json.loads(results)["tests"]
        print(tests, file=sys.stderr)
        score = reduce(lambda x,y: x+y, list(map(lambda x: x["score"], tests)))
        print(score, file=sys.stderr)

        submission_data["score"] = score
        
        db.session.query(Submission).filter_by(id=new_uuid).update(submission_data)
        db.session.commit()

        new_submission = db.session.query(Submission).filter_by(id=new_uuid)
        new_submission = SubmissionSchema().dump(new_submission, many=True)[0]

        return jsonify(new_submission)

    if file and not allowed_file(file.filename):
        return "invalid extension"

@submission.route('/upload_assignment_autograder', methods=["POST", "GET"])
@cross_origin()
def upload_assignment_autograder():
    '''
    /upload_assignment_autograder uploads an autograder to the database
    @param file             the autograder
    @param assignment_id    the id of an assignment
    '''
    if "file" not in request.files:
        flash("No file part")
        return "no file", 400
    file = request.files["file"]
    assignment_id = request.form["assignment_id"]

    if file.filename == "":
        flash("No selected file")
        return "no selected file", 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # File stored in the filepath given by assignment_dir (currently usr/app/assignments), 
        # file saved locally in backend/assignments as well
        docker_client.saveFile(file, filename, docker_client.assignment_dir, False)

        file.seek(0)
        assignment_data = {
            'autograder_file': None, #file.read(),
        }

        db.session.query(Assignment).filter_by(id=assignment_id).update(assignment_data)
        assignment = db.session.query(Assignment).filter_by(id=assignment_id)
        db.session.commit()

        assignment = AssignmentSchema().dump(assignment, many=True)[0]

        return jsonify(assignment)
    else:
        flash("Something went wrong")
        return "something went wrong (probably bad file)", 400