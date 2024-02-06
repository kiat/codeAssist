import uuid
import docker_client
import json
import sys
from werkzeug.utils import secure_filename
from functools import reduce
from flask import Blueprint, request, jsonify, flash
from flask_cors import cross_origin
from api import db
from api.models import Assignment, Submission, Student, Enrollment
from api.schemas import AssignmentSchema, SubmissionSchema, StudentSchema, EnrollmentSchema
from datetime import datetime 
from time import time 
from sqlalchemy import desc, func
import base64


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

@submission.route('/get_latest_submission', methods=["GET"])
@cross_origin()
def get_latest_submission():
    '''
    /get_latest_submission gets the latest submission by a student for an assignment
    Requires from the frontend a JSON containing:
    @param student_id       the id of a student
    @param assignment_id    the id of an assignment
    '''
    student_id = request.args.get("student_id")
    assignment_id = request.args.get("assignment_id")

    submission = (db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id)
                    .order_by(desc(Submission.executed_at)).limit(1))
    
    submission = SubmissionSchema().dump(submission, many=True)
    
    return jsonify(submission)
    
@submission.route('/upload_submission', methods=["POST", "GET"]) #TODO: remove get
@cross_origin()
def upload_submission():
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


    # # Exception handling is needed. 
    # student_name = db.session.query(Student).filter_by(id=student_id)
    # student_name = StudentSchema().dump(student_name, many=True)

    # # There should be only one Student coming back. 
    # name = student_name[0]["name"]
    # print("Student Name is: ", name)


    if file.filename == "":
        flash("No selected file")
        return "no selected file"
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        new_uuid = str(uuid.uuid4())

        submission_data = {
            "id": new_uuid,
            # "name": name,
            "student_id": student_id,
            "assignment_id": assignment_id,
            "student_code_file": file.read(),
            "completed": False
        }

        file.seek(0)

        db.session.add(Submission(**submission_data))
        db.session.commit()


        # We time the execution of user submission. 
        before = time()
            
        # Adding the timestamp of this submission, executed_at in database 
        timestamp = datetime.utcfromtimestamp(before).strftime('%Y-%m-%d %H:%M:%S')
        # We add the executed time even if this run fails. 
        submission_data["executed_at"] = timestamp
        submission_data["completed"] = False
        
        try:
            logs, results = docker_client.run_container(assignment, file, filename, new_uuid)

        except Exception as my_exception:
            # This should be refactored later for better exception handling.
            print("Could not run this because of some error regarding submitted file or our execution of it!")
            print(my_exception)
            # submission_data["execution_time"] = elapsed_time

            db.session.query(Submission).filter_by(id=new_uuid).update(submission_data)
            db.session.commit()

            submission_data["results"] = None

            new_submission = db.session.query(Submission).filter_by(id=new_uuid)
            new_submission = SubmissionSchema().dump(new_submission, many=True)[0]
            return jsonify(new_submission)

                
        after = time()
        elapsed_time = after - before 
        
        # Elapsed time in Milliseconds. 
        submission_data["execution_time"] = elapsed_time
        submission_data["results"] = results.encode('utf8')
        
        # When is this false!?
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
    
@submission.route('/get_results', methods=["GET"])
@cross_origin(origins='*')
def get_results():
    '''
    /get_results gets reseults of a student's submission
    useful for instructor side view to view student's results
    Requires from the frontend a JSON containing:
    @param email       the email_address of a student
    @param assignment_id    the id of an assignment
    '''
    email = request.args.get("email")
    assignment_id = request.args.get("assignment_id")

    student = db.session.query(Student).filter_by(email_address=email).first()
    if student:
        student_id = student.id

    submission = (db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id)
                    .order_by(desc(Submission.executed_at)).limit(1))
    submission = SubmissionSchema().dump(submission, many=True)
    
    return jsonify(submission)

# This is simpler, but fails to get the students who did not submit
# @submission.route('/get_course_assignment_latest_submissions', methods=["GET"])
# @cross_origin()
# def get_course_assignment_latest_submissions():
#     course_id = request.args.get("course_id")
#     assignment_id = request.args.get("assignment_id")

#     # for each student, find the latest submission executed_at time 
#     latest_submissions_time = db.session.query(
#         Submission.student_id,
#         func.max(Submission.executed_at).label('latest_executed_at')
#     ).filter(
#         Submission.assignment_id == assignment_id
#     ).group_by(
#         Submission.student_id
#     ).subquery()

#     # find latest submission for each student
#     latest_submissions = db.session.query(Submission, Student).join(
#         Student, Student.id == Submission.student_id
#     ).join(
#         latest_submissions_time, 
#         (Submission.student_id == latest_submissions_time.c.student_id) &
#         (Submission.executed_at == latest_submissions_time.c.latest_executed_at)
#     ).filter(
#         Enrollment.student_id == Student.id,
#         Enrollment.course_id == course_id
#     ).all()

#     submission_data = []
#     for submission, student in latest_submissions:
#         submission_info = {
#             "student_name": student.name,
#             "email_address": student.email_address,
#             "score": submission.score,
#             "executed_at": submission.executed_at,
#         }
#         submission_data.append(submission_info)

#     return jsonify(submission_data)

@submission.route('/get_course_assignment_latest_submissions', methods=["GET"])
@cross_origin()
def get_course_assignment_latest_submissions():
    course_id = request.args.get("course_id")
    assignment_id = request.args.get("assignment_id")

    # 1) Find all students enrolled in the course
    enrolled_students = db.session.query(Enrollment.student_id).filter_by(course_id=course_id).all()

    submission_data = []
    for student in enrolled_students:
        student_id = student.student_id

        # 2) Find the latest submission for each student for the given assignment
        latest_submission = db.session.query(Submission).filter_by(
            student_id=student_id, assignment_id=assignment_id
        ).order_by(desc(Submission.executed_at)).first()

        # 3) Get student details
        student_details = db.session.query(Student).filter_by(id=student_id).first()

        if latest_submission:
            submission_info = {
                "student_name": student_details.name,
                "email_address": student_details.email_address,
                "score": latest_submission.score,
                "executed_at": latest_submission.executed_at
            }
        else:
            # if a student hasn't submitted the assignment
            submission_info = {
                "student_name": student_details.name,
                "email_address": student_details.email_address,
            }

        submission_data.append(submission_info)

    return jsonify(submission_data)