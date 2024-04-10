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
                    .order_by(desc(Submission.submitted_at)).limit(1))
    
    submission = SubmissionSchema().dump(submission, many=True)
    
    return jsonify(submission)


@submission.route('/upload_submission', methods=["POST"])
@cross_origin()
def upload_submission():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    assignment_id = request.form.get("assignment_id")
    student_id = request.form.get("student_id")
    
    if not assignment_id or not student_id or file.filename == "":
        return jsonify({"error": "Missing assignment ID, student ID, or no selected file"}), 400

    filename = secure_filename(file.filename)
    submissions_dir = os.path.abspath(os.path.join('routes', 'upload_autograderSCOPE', 'runs', assignment_id, "submissions"))
    results_dir = os.path.abspath(os.path.join('routes', 'upload_autograderSCOPE', 'runs', assignment_id, student_id, 'results'))
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(submissions_dir, exist_ok=True)
    
    file_path = os.path.join(submissions_dir, filename)
    file.save(file_path)

    # Correcting volume mount paths to match the expected directory structure
    submission_volume_mount = f"{file_path}:/autograder/submission/{filename}"
    results_volume_mount = f"{results_dir}:/autograder/results"
    
    container_name = f"ag_{assignment_id}_{student_id}_{int(time.time())}"

    docker_run_cmd = [
        "docker", "run", "--name", container_name,
        "-v", submission_volume_mount,
        "-v", results_volume_mount,
        f"autograder-{assignment_id}"
    ]
    
    run_proc = subprocess.run(docker_run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if run_proc.returncode != 0:
        subprocess.run(['docker', 'rm', '-f', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return jsonify({"error": "Failed to run Docker container", "details": run_proc.stderr.decode()}), 500

    container_results_path = f"/autograder/results/results.json"
    host_results_path = os.path.join(results_dir, 'results.json')
    
    copy_proc = subprocess.run(['docker', 'cp', f"{container_name}:{container_results_path}", host_results_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if copy_proc.returncode != 0:
        subprocess.run(['docker', 'rm', '-f', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return jsonify({"error": "Failed to copy results from Docker container", "details": copy_proc.stderr.decode()}), 500

    subprocess.run(['docker', 'rm', '-f', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    with open(host_results_path, 'r') as f:
        results_data = json.load(f)

    return jsonify({"message": "Submission uploaded and autograded successfully", "results": results_data}), 200


@submission.route('/upload_assignment_autograder', methods=["POST"])
@cross_origin()
def upload_assignment_autograder():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    assignment_id = request.form.get("assignment_id")

    if not assignment_id or file.filename == "":
        return jsonify({"error": "Missing assignment ID or no selected file"}), 400

    filename = secure_filename(file.filename)
    assignment_dir = os.path.join('routes', 'upload_autograderSCOPE', 'runs', assignment_id)
    os.makedirs(assignment_dir, exist_ok=True)
    filepath = os.path.join(assignment_dir, filename)
    submission_dir = os.path.join(assignment_dir, 'submission')
    os.makedirs(submission_dir, exist_ok=True)

    file.save(filepath)

    # Unzip the autograder file
    try:
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(os.path.join(assignment_dir, "source"))
    except zipfile.BadZipFile:
        return jsonify({"error": "Uploaded file is not a valid zip file"}), 400

    # Generate Dockerfile in the assignment directory
    dockerfile_content = """
FROM python:3.9

RUN apt-get update && apt-get install -y python3-pip python3-dev && rm -rf /var/lib/apt/lists/*

COPY source /autograder/source
COPY submission /autograder/submission

RUN chmod +x /autograder/source/setup.sh && \\
    /autograder/source/setup.sh

RUN chmod +x /autograder/source/run_autograder

WORKDIR /autograder

ENTRYPOINT ["/bin/bash", "/autograder/source/run_autograder"]
"""
    with open(os.path.join(assignment_dir, 'Dockerfile'), 'w') as dockerfile:
        dockerfile.write(dockerfile_content.strip())

    # Build the Docker image
    docker_build_cmd = ["docker", "build", "-t", f"autograder-{assignment_id}", assignment_dir]
    build_proc = subprocess.run(docker_build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if build_proc.returncode != 0:
        return jsonify({"error": "Failed to build Docker image", "details": build_proc.stderr.decode()}), 500

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
