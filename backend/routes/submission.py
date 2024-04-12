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
import docker 
import zipfile
import shutil
import time

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


    
@submission.route('/upload_submission', methods=["POST"])
@cross_origin()
def upload_submission():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    assignment_id = request.form.get("assignment_id")
    student_id = request.form.get("student_id")
    if not assignment_id or not student_id or not file.filename:
        return jsonify({"error": "Missing required parameters or file"}), 400

    filename = secure_filename(file.filename)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assignment_dir = os.path.join(current_dir, 'upload_autograder', 'runs', assignment_id)
    submissions_dir = os.path.join(assignment_dir, "submission")
    results_dir = os.path.join(assignment_dir, student_id, 'results')
    for directory in [submissions_dir, results_dir]:
        os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(submissions_dir, filename)
    file.save(file_path)


    # Write the Dockerfile
    dockerfile_content = """
    FROM python:3.9
    RUN apt-get update && apt-get install -y python3-pip python3-dev && rm -rf /var/lib/apt/lists/*
    COPY source /autograder/source
    COPY submission /autograder/submission
    RUN chmod +x /autograder/source/setup.sh && /autograder/source/setup.sh
    RUN chmod +x /autograder/source/run_autograder
    RUN mkdir -p /autograder/results
    WORKDIR /autograder
    CMD ["/bin/bash", "/autograder/source/run_autograder"]
    """
    with open(os.path.join(assignment_dir, 'Dockerfile'), 'w') as dockerfile:
        dockerfile.write(dockerfile_content)

    os.chdir(assignment_dir)
    build_proc = subprocess.run(f"docker build -t autograder-{assignment_id} .".split(), capture_output=True)
    if build_proc.returncode != 0:
        os.chdir(current_dir)
        return jsonify({"error": "Failed to build Docker image", "details": build_proc.stderr.decode()}), 500

    container_name = f"ag_{assignment_id}_{student_id}"
    run_proc = subprocess.run(f"docker run -d --name {container_name} autograder-{assignment_id} tail -f /dev/null".split(), capture_output=True)
    if run_proc.returncode != 0:
        os.chdir(current_dir)
        return jsonify({"error": "Failed to start Docker container", "details": run_proc.stderr.decode()}), 500

    exec_proc = subprocess.run(f"docker exec {container_name} /bin/bash /autograder/source/run_autograder".split(), capture_output=True)
    if exec_proc.returncode != 0:
        os.chdir(current_dir)
        return jsonify({"error": "Autograder execution failed", "details": exec_proc.stderr.decode()}), 500

    cat_proc = subprocess.run(f"docker exec {container_name} cat /autograder/results/results.json".split(), capture_output=True)
    if cat_proc.returncode != 0:
        os.chdir(current_dir)
        return jsonify({"error": "Failed to read results.json", "details": cat_proc.stderr.decode()}), 500

    results_json_content = cat_proc.stdout.decode()
    host_results_json_path = os.path.join(results_dir, 'results.json')
    with open(host_results_json_path, 'w') as file:
        file.write(results_json_content)

    # Query the database for the number of previous submissions
    submission_count = db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id).count()

    # Create a new submission record
    new_submission = Submission(
        id=uuid.uuid4(),
        student_id=uuid.UUID(student_id),
        assignment_id=uuid.UUID(assignment_id),
        student_code_file=open(file_path, 'rb').read(),
        results=open(host_results_json_path, 'rb').read(),
        score=sum(test['score'] for test in json.loads(results_json_content)['tests']),
        execution_time=float(json.loads(results_json_content).get('execution_time', 0)),
        submitted_at=datetime.now(),
        completed=True,
        submission_number=submission_count + 1
    )
    db.session.add(new_submission)
    db.session.commit()

    subprocess.run(f"docker stop {container_name}".split(), capture_output=True)
    subprocess.run(f"docker rm {container_name}".split(), capture_output=True)
    os.chdir(current_dir)
    
    return jsonify({"message": "Submission uploaded and autograded successfully", "results_path": host_results_json_path}), 200



@submission.route('/upload_assignment_autograder', methods=["POST"])
@cross_origin()
def upload_assignment_autograder():
    # Validate input file and parameters
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    assignment_id = request.form.get("assignment_id")
    if not assignment_id or not file.filename:
        return jsonify({"error": "Missing assignment ID or no selected file"}), 400

    # Set up paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assignment_dir = os.path.join(current_dir, 'upload_autograder', 'runs', assignment_id)
    os.makedirs(assignment_dir, exist_ok=True)

    # Save the uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(assignment_dir, filename)
    file.save(filepath)

    # Extract the contents of the uploaded ZIP file
    try:
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(os.path.join(assignment_dir, "source"))
    except zipfile.BadZipFile:
        return jsonify({"error": "Uploaded file is not a valid zip file"}), 400

    return jsonify({"message": "Autograder uploaded and Docker image generated successfully", "image_name": f"autograder-{assignment_id}"}), 200
    
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
