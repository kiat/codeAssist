import uuid
import docker_client
import json
import sys
from werkzeug.utils import secure_filename
from functools import reduce
from flask import Blueprint, request, jsonify, flash
from flask_cors import cross_origin
from api import db
from api.models import Assignment, Submission, Student, Enrollment, TestCaseResult, TestCase
from api.schemas import AssignmentSchema, SubmissionSchema, StudentSchema, EnrollmentSchema
from datetime import datetime, timezone
import subprocess
import os
import hashlib

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
    
# @submission.route('/upload_submission', methods=["POST", "GET"])
# @cross_origin()
# def upload_submission():
#     print(request.files)
#     print(request.form)
#     if "file" not in request.files:
#         flash("No file part")
#         return "no file\n"
#     file = request.files["file"]
#     assignment = request.form["assignment"].lower()
#     student_id = request.form["student_id"]
#     assignment_id = request.form["assignment_id"]

#     if file.filename == "":
#         flash("No selected file")
#         return "no selected file"
#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         new_uuid = str(uuid.uuid4())

#         submission_data = {
#             "id": new_uuid,
#             "student_id": student_id,
#             "assignment_id": assignment_id,
#             "student_code_file": file.read(),
#             "completed": False,
#             "score": 0,
#         }

#         file.seek(0)

#         db.session.add(Submission(**submission_data))
#         db.session.commit()

#         before = time()
#         # timestamp = datetime.fromtimestamp(before, datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')
#         timestamp = datetime.fromtimestamp(before, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
#         submission_data["executed_at"] = timestamp
#         submission_data["completed"] = False

#         logs = None  
#         results = None

#         try:
#             logs, results = docker_client.run_container(assignment, file, filename, new_uuid)
#         except Exception as my_exception:
#             print("Could not run this because of some error regarding submitted file or our execution of it!")
#             print(my_exception)
                  
#             debug_info = {
#                 "error": str(my_exception),
#                 "logs": logs if logs else None
#             }

#             submission_data["results"] = None
#             submission_data["debug_info"] = debug_info

#             db.session.query(Submission).filter_by(id=new_uuid).update(submission_data)
#             db.session.commit()

#             new_submission = db.session.query(Submission).filter_by(id=new_uuid)
#             new_submission = SubmissionSchema().dump(new_submission, many=True)[0]
#             new_submission["debug_info"] = debug_info

#             return jsonify(new_submission)

#         after = time()
#         elapsed_time = after - before

#         submission_data["execution_time"] = elapsed_time

#         debug_info = {
#             "raw_results": results,
#             "results_type": str(type(results)),
#             "parsed_results": None,
#             "score_calculation_error": None
#         }

#         try:
#             parsed_results = json.loads(results)
#             debug_info["parsed_results"] = parsed_results

#             tests = parsed_results["tests"]
#             score = reduce(lambda x, y: x + y, list(map(lambda x: x["score"], tests)))
#             submission_data["score"] = score
#         except (json.JSONDecodeError, KeyError) as e:
#             debug_info["score_calculation_error"] = str(e)
#             submission_data["score"] = 0

#         submission_data["results"] = results.encode('utf8')
#         submission_data["completed"] = True

#         db.session.query(Submission).filter_by(id=new_uuid).update(submission_data)
#         db.session.commit()

#         new_submission = db.session.query(Submission).filter_by(id=new_uuid)
#         new_submission = SubmissionSchema().dump(new_submission, many=True)[0]

#         new_submission["debug_info"] = debug_info

#         return jsonify(new_submission)

#     if file and not allowed_file(file.filename):
#         return "invalid extension"

@submission.route('/upload_submission', methods=["POST", "GET"])
@cross_origin()
def upload_submission():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    student_id = request.form.get("student_id", "")
    assignment_id = request.form.get("assignment_id", "")

    if file.filename == "":
        return jsonify({"error": "No selected file or invalid file type"}), 400

    filename = secure_filename(file.filename)
    hash_str = hashlib.sha1(f"{assignment_id}_{student_id}".encode()).hexdigest()[:10]
    submission_dir = os.path.join('routes', 'upload_submissions', 'runs', hash_str)
    test_cases_dir = os.path.join(submission_dir, 'test_cases')
    submission_dir_abs = os.path.abspath(test_cases_dir)

    if not os.path.exists(submission_dir_abs):
        os.makedirs(submission_dir_abs)

    filepath = os.path.join(submission_dir_abs, filename)
    file.seek(0)  # Reset file pointer before reading
    file_content = file.read()  # Read file content to save to database
    file.seek(0)  # Reset file pointer again for Docker operations

    # new_submission = Submission(
    #     student_id=student_id,
    #     assignment_id=assignment_id,
    #     student_code_file=file_content,
    #     completed=False
    # )
    # db.session.add(new_submission)
    # db.session.commit()

    # Proceed with Docker operations
    docker_build_cmd = f"docker build --build-arg HASH_STR={hash_str} -t student_grader_{hash_str} -f ./routes/upload_submissions/Dockerfile ."
    docker_run_cmd = f"docker run --name sg_{hash_str} -e FILENAME={filename} -e HASH_STR={hash_str} student_grader_{hash_str}"

    build_proc = subprocess.run(docker_build_cmd.split(), capture_output=True)
    if build_proc.returncode != 0:
        return jsonify({"error": "Failed to build Docker image", "details": build_proc.stderr.decode()}), 500

    run_proc = subprocess.run(docker_run_cmd.split(), capture_output=True)
    if run_proc.returncode != 0:
        return jsonify({"error": "Failed to run Docker container", "details": run_proc.stderr.decode()}), 500

    # Assuming the container writes results to results.json in the mounted directory
    results_json_path = os.path.join(submission_dir_abs, 'results.json')
    if os.path.exists(results_json_path):
        with open(results_json_path, 'r') as results_file:
            results_data = json.load(results_file)
        # Update the submission record with results
        # new_submission.results = json.dumps(results_data).encode('utf-8')  # Ensure results are saved as bytes
        # new_submission.completed = True
        # db.session.commit()
    else:
        return jsonify({"error": "Results file not found after container execution"}), 500

    # Clean up Docker resources
    subprocess.run(f"docker rm sg_{hash_str}".split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(f"docker rmi student_grader_{hash_str}".split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return jsonify({"message": "Submission processed successfully", "results": results_data}), 200


@submission.route('/upload_assignment_autograder', methods=["POST", "GET"])
@cross_origin()
def upload_assignment_autograder():
    if "file" not in request.files:
        flash("No file part")
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    assignment_id = request.form["assignment_id"]

    if file.filename == "":
        flash("No selected file")
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        assignment_dir = os.path.join('routes', 'upload_autograder', 'runs', assignment_id)
        if not os.path.exists(assignment_dir):
            os.makedirs(assignment_dir)
        filepath = os.path.join(assignment_dir, filename)
        file.save(filepath)

        docker_build_cmd = f"docker build -t autograder_{assignment_id} ./routes/upload_autograder/"
        docker_run_cmd = f"docker run --name ag_{assignment_id} -e ASSIGNMENT_ID={assignment_id} -e FILENAME={filename} autograder_{assignment_id}"

        build_proc = subprocess.run(docker_build_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if build_proc.returncode != 0:
            return jsonify({"error": "Failed to build Docker image", "details": build_proc.stderr.decode()}), 500

        run_proc = subprocess.run(docker_run_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if run_proc.returncode != 0:
            return jsonify({"error": "Failed to run Docker container", "details": run_proc.stderr.decode()}), 500

        # Define the path where the results.json is expected to be in the container
        container_results_path = f"ag_{assignment_id}:/app/results.json"
        # Define the path where you want to copy results.json on your host
        host_results_path = os.path.join(assignment_dir, 'results.json')

        # Copy results.json from the container to the host
        copy_proc = subprocess.run(['docker', 'cp', container_results_path, host_results_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if copy_proc.returncode != 0:
            return jsonify({"error": "Failed to copy results from Docker container", "details": copy_proc.stderr.decode()}), 500

        # Now, read the copied results.json and process it
        with open(host_results_path, 'r') as f:
            results_data = json.load(f)

        # logic to process and insert the data into the database
        for test_case in results_data['test_cases']:
            new_test_case = TestCase(
                id=uuid.uuid4(),
                assignment_id=assignment_id,
                test_case_name=test_case['test_case_name'],
                input_data=test_case['input'],
                expected_output=test_case['output']
            )
            db.session.add(new_test_case)
        db.session.commit()


        # Clean up Docker container and image after the operation
        subprocess.run(f"docker rm ag_{assignment_id}".split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(f"docker rmi autograder_{assignment_id}".split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return jsonify({"message": "Autograder executed successfully", "results": results_data}), 200
    else:
        flash("Something went wrong")
        return jsonify({"error": "Something went wrong (probably bad file)"}), 400
    
    
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


# curl -X POST http://localhost:5000/upload_submission \
#   -H "Content-Type: multipart/form-data" \
#   -F "assignment=assignment1" \
#   -F "student_id=f8244880-f243-4fe4-a3a4-66e1d7c1f388" \
#   -F "assignment_id=96d2451d-6c47-4148-9dcc-092c7728f84d" \
#   -F "file=@dna.py"
