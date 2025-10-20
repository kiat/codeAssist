import uuid
import json
import sys
import io
import tarfile
import subprocess
import os
import docker 
import shutil
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from functools import reduce
from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS, cross_origin
from api import db
from api.models import Assignment, Submission, User, Enrollment, TestCaseResult, TestCase
from api.schemas import AssignmentSchema, SubmissionSchema, UserSchema, EnrollmentSchema
from util.errors import BadRequestError, InternalProcessingError, ConflictError, NotFoundError, ServerTimeoutError, SubmissionTimeoutError
from datetime import datetime, timezone
from sqlalchemy import desc, func
from ai_integration import async_get_ai_feedback
import threading
import json


submission = Blueprint('submission', __name__)
docker_client = docker.from_env()

ALLOWED_EXTENSIONS = {'py','zip'}

def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@submission.route('/get_submissions', methods=["GET"])
@cross_origin()
def get_submissions():
    '''
    /get_submissions gets all submissions by a student for an assignment
    Requires from the frontend a JSON containing:
    @param student_id       the id of a student
    @param assignment_id    the id of an assignment
    '''
    student_id = request.args.get("student_id")
    assignment_id = request.args.get("assignment_id")

    if not student_id or not assignment_id:
        return jsonify({"error": "Missing student_id or assignment_id"}), 400

    submissions = db.session.query(Submission).filter_by(
        student_id=student_id, 
        assignment_id=assignment_id
    ).all()  

    if not submissions:
        return jsonify({"message": "No submissions found for the provided student and assignment"}), 404

    submission_schema = SubmissionSchema(many=True)
    result = submission_schema.dump(submissions)

    return jsonify(result)


    
@submission.route('/upload_submission', methods=["POST"])
@cross_origin()
def upload_submission():
    if "file" not in request.files:
        raise BadRequestError("No file part")
    file = request.files["file"]
    assignment_id = request.form.get("assignment_id")
    student_id = request.form.get("student_id")
    if not assignment_id or not student_id or not file.filename:
        raise BadRequestError("Missing required fields")

    filename = secure_filename(file.filename)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assignment_dir = os.path.join(current_dir, 'upload_autograder', 'runs', assignment_id)
    submission_uuid = uuid.uuid4().hex[:8]
    submissions_dir = os.path.join(assignment_dir, "submission", submission_uuid)
    results_dir = os.path.join(assignment_dir, student_id, 'results')
    
    for directory in [submissions_dir, results_dir]:
        os.makedirs(directory, exist_ok=True)
    
    for filenames in os.listdir(submissions_dir):
        file_path = os.path.join(submissions_dir, filenames)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
            raise InternalProcessingError("Failed to grade submission")
    file_path = os.path.join(submissions_dir, filename)

    file.save(file_path)

    #get autograder if it exists
    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()


    if not assignment or not assignment.autograder_image_name or assignment.autograder_image_name.strip() == "":
        submission_count = db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id).count()
        old = db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id, active=True)
        if old:
            old.update({'active': False})
        
        new_submission = Submission(
            id=uuid.uuid4(),
            file_name=filename,
            student_id=uuid.UUID(student_id),
            assignment_id=uuid.UUID(assignment_id),
            student_code_file=open(file_path, 'rb').read(),
            results=None,
            score=None,
            execution_time=0.0,
            submitted_at=datetime.now(),
            active=True,
            completed=True,
            submission_number=submission_count + 1,
            ai_feedback=None
        )

        db.session.add(new_submission)
        db.session.commit()

        return jsonify({
            "message": "Submission uploaded. No autograder found.",
            "submissionID": str(new_submission.id)
        }), 200


    # Create a new temporary container from the assignment image
    temp_container_name = f"submission_{uuid.uuid4().hex[:8]}"
    container = docker_client.containers.run(
        image=assignment.autograder_image_name,
        name=temp_container_name,
        detach=True,
        tty=True,
        command="tail -f /dev/null"  # Keep container alive for copying & exec
    )

    try:
        # Copy the submission into /autograder/submission/
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            tar.add(file_path, arcname=filename)
        tar_stream.seek(0)
        container.put_archive("/autograder/submission/", tar_stream)

        # Run the autograder inside the container
        exec_proc = subprocess.run(
            f"docker exec {temp_container_name} /bin/bash /autograder/source/run_autograder".split(),
            capture_output=True,
            timeout=assignment.autograder_timeout
        )

    except subprocess.TimeoutExpired:
        # clean up container
        container.stop()
        container.remove()
        os.chdir(current_dir)

        # upload failed submission to db
        timeout_result = {
            "tests": [
                {
                    "name": "Submission Timeout",
                    "score": 0,
                    "max_score": 0,
                    "status": "failed",
                    "output": "The submission did not complete within the time limit."
                }
            ],
            "leaderboard": [],
            "visibility": "visible",
            "execution_time": f"{assignment.autograder_timeout:.2f}",
            "score": 0
        }

        submission_count = db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id).count()
        old = db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id, active=True)
        if old:
            old.update({'active': False})
        
        failed_submission = Submission(
            id=uuid.uuid4(),
            file_name=filename,
            student_id=uuid.UUID(student_id),
            assignment_id=uuid.UUID(assignment_id),
            student_code_file=open(file_path, 'rb').read(),
            results=json.dumps(timeout_result).encode(),
            score=0,
            execution_time=float(assignment.autograder_timeout),
            submitted_at=datetime.now(),
            active=True,
            completed=False,
            submission_number=submission_count + 1,
            ai_feedback=None
        )
        db.session.add(failed_submission)
        db.session.commit()

        raise SubmissionTimeoutError("Submitted program took too long to run", failed_submission.id)

    if exec_proc.returncode != 0:
        os.chdir(current_dir)
        print(f"Error: Autograder failed, details: {exec_proc.output.decode()}")
        raise InternalProcessingError("Failed to grade submission")

    # get results
    cat_result = container.exec_run("cat /autograder/results/results.json")
    if cat_result.exit_code != 0:
        os.chdir(current_dir)
        print(f"Error: Failed to retrieve results.json, details: {cat_result.output.decode()}")
        raise InternalProcessingError("Failed to grade submission")

    results_json_content = cat_result.output.decode()
    submission_uuid = uuid.uuid4().hex[:8]
    host_results_json_path = os.path.join(results_dir, f'results_{submission_uuid}.json')
    with open(host_results_json_path, 'w') as file:
        file.write(results_json_content)

    # Update active submission in db
    submission_count = db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id).count()
    old = db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id, active=True)
    if old:
        old.update({'active': False})

    # Create a new submission record. Note that we add an initial value (e.g. None) for ai_feedback.
    new_submission = Submission(
        id=uuid.uuid4(),
        file_name=filename,
        student_id=uuid.UUID(student_id),
        assignment_id=uuid.UUID(assignment_id),
        student_code_file=open(file_path, 'rb').read(),
        results=open(host_results_json_path, 'rb').read(),
        score=json.loads(results_json_content)['score'],
        execution_time=float(json.loads(results_json_content).get('execution_time', 0)),
        submitted_at=datetime.now(),
        #set the active to true for a newly submitted submission
        active=True,
        completed=True,
        submission_number=submission_count + 1,
        ai_feedback=None  # Initially no AI feedback
    )
    db.session.add(new_submission)
    db.session.commit()

    # Clean up container
    container.stop()
    container.remove()
    os.chdir(current_dir)

    # Capture the app object and launch a background thread to get AI feedback asynchronously.
    app_obj = current_app._get_current_object()
    threading.Thread(
        target=async_get_ai_feedback, 
        args=(app_obj, new_submission.id, file_path, results_json_content)
    ).start()

    # Return the response. Note that ai_feedback might not be available immediately.
    return jsonify({
        "message": "Submission uploaded and autograded successfully",
        "results_path": host_results_json_path,
        "submissionID": str(new_submission.id)
    }), 200



@submission.route('/upload_assignment_autograder', methods=["POST"])
@cross_origin()
def upload_assignment_autograder():
    if "file" not in request.files:
        raise BadRequestError("No file part")
    file = request.files["file"]
    assignment_id = request.form.get("assignment_id")
    autograder_timeout = request.form.get("autograder_timeout")
    if not assignment_id or not file.filename:
        raise BadRequestError("Missing required fields")

    # Set up paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assignment_dir = os.path.join(current_dir, 'upload_autograder', 'runs', assignment_id)
    os.makedirs(assignment_dir, exist_ok=True)

    # Remove old zip files
    for filename in os.listdir(assignment_dir):
        if filename.endswith(".zip"):
            os.remove(os.path.join(assignment_dir, filename))

    # Save new zip file
    filename = secure_filename(file.filename)
    filepath = os.path.join(assignment_dir, filename)
    file.save(filepath)

    # Check assignment exists
    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    # Write Dockerfile
    dockerfile_content = """
    FROM python:3.9-slim
    RUN apt-get update && apt-get install -y --no-install-recommends python3-pip python3-dev unzip && rm -rf /var/lib/apt/lists/*
    COPY *.zip /autograder/
    RUN unzip /autograder/*.zip -d /autograder/source && \\
        chmod +x /autograder/source/setup.sh && /autograder/source/setup.sh && \\
        chmod +x /autograder/source/run_autograder && \\
        mkdir -p /autograder/results /autograder/submission
    WORKDIR /autograder
    CMD ["/bin/bash", "/autograder/source/run_autograder"]
    """
    with open(os.path.join(assignment_dir, 'Dockerfile'), 'w') as f:
        f.write(dockerfile_content)

    # Build image
    try:
        image_name = f"autograder-{assignment_id}"
        docker_client.images.build(path=assignment_dir, tag=image_name)
    except docker.errors.BuildError as e:
        print("Build failed:", e)
        raise InternalProcessingError("Failed to build Docker image")

    # Save image name and timeout to assignment
    assignment.autograder_image_name = image_name
    assignment.autograder_timeout = autograder_timeout
    db.session.commit()

    return jsonify({
        "message": "Autograder uploaded and Docker image built successfully",
        "image_name": image_name
    }), 200


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

    student = db.session.query(User).filter_by(email_address=email).first()
    if student:
        student_id = student.id

    submission = (db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id)
                    .order_by(desc(Submission.submitted_at)).limit(1))
    submission = SubmissionSchema().dump(submission, many=True)
    
    return jsonify(submission)


@submission.route('/get_latest_submission', methods=["GET"])
@cross_origin()
def get_latest_submission():
    student_id = request.args.get("student_id")
    assignment_id = request.args.get("assignment_id")

    if not student_id or not assignment_id:
        return jsonify({"error": "Missing student_id or assignment_id"}), 400

    # Query for the latest submission based on the submitted time
    latest_submission = Submission.query.filter_by(
        student_id=student_id,
        assignment_id=assignment_id
    ).order_by(Submission.submitted_at.desc()).first()

    # Serialize the submission data
    submission_schema = SubmissionSchema()

    if not latest_submission:
        # Return an empty object instead of an error
        return jsonify({"message": "No submissions found", "data": submission_schema.dump(None)}), 200

    submission_data = submission_schema.dump(latest_submission)
    return jsonify(submission_data), 200

@submission.route('/get_all_assignment_submissions', methods=["GET"])
@cross_origin()
def get_all_assignment_submissions():
    assignment_id = request.args.get("assignment_id")

    if not assignment_id:
        return jsonify({"error": "Missing assignment_id"}), 400

    # Query for all submissions related to the assignment
    all_submissions = Submission.query.filter_by(
        assignment_id=assignment_id
    ).order_by(Submission.submitted_at.desc()).all()

    if not all_submissions:
        return jsonify({"error": "No submissions found for this assignment"}), 404

    # Serialize the submission data
    submissions_schema = SubmissionSchema(many=True)  # Set 'many=True' to handle multiple objects
    submissions_data = submissions_schema.dump(all_submissions)

    return jsonify(submissions_data), 200


@submission.route('/delete_submission', methods=["DELETE"])
@cross_origin()
def delete_submission():
    submission_id = request.args.get("submission_id")

    if not submission_id:
        return jsonify({"error": "Missing submission_id"}), 400

    # Query for the submission to be deleted by submission_id
    submission_to_delete = db.session.get(Submission, submission_id)

    if not submission_to_delete:
        # If no submission is found, return an error message
        return jsonify({"message": "No submission found to delete"}), 404

    # If a submission is found, delete it from the database
    db.session.delete(submission_to_delete)
    db.session.commit()

    # Return a success message
    return jsonify({"message": "Submission successfully deleted"}), 200

@submission.route('/get_submission_details', methods=["GET"])
@cross_origin()
def get_submission_details():
    '''
    /get_student_by_id gets the submission details from the db
    Requires from the frontend a JSON containing:
    @param submission_id    the submission id
    '''
    id = request.args.get("submission_id")

    if not id:
        return jsonify({"error": "Missing submission id"}), 400
    
    submission_to_get = db.session.query(Submission).filter_by(id=id)

    if not submission_to_get:
        # If no submission is found, return an error message
        return jsonify({"message": "No submission found"}), 404
    
    submission = SubmissionSchema().dump(submission_to_get, many=True)[0]

    return jsonify(submission), 200

@submission.route('/get_active_submission', methods=["GET"])
@cross_origin()
def get_active_submission():
    '''

    '''
    student = request.args.get("student_id")
    assignment = request.args.get("assignment_id")

    if not assignment or not student:
      raise BadRequestError("not sufficient details")
    
    submission = db.session.query(Submission).filter_by(assignment_id=assignment, student_id=student, active=True).first()

    if not submission:
        return jsonify({"message": "no such submission found"})
    
    details = SubmissionSchema().dump(submission)

    return jsonify(details), 200


@submission.route('/activate_submission', methods=["POST"])
@cross_origin()
def activate_submission():
    '''
    Activates a submission and deactivates any currently active submission for the same assignment and student.
    Requires from the frontend a JSON containing:
    @param submission_id    the id of the submission to activate
    @param student_id       the id of the student
    @param assignment_id    the id of the assignment
    '''
    data = request.json
    submission_id = data.get('submission_id')
    student_id = data.get('student_id')
    assignment_id = data.get('assignment_id')

    if not submission_id or not student_id or not assignment_id:
        return jsonify({"error": "Missing submission_id, student_id or assignment_id"}), 400

    try:
        # Deactivate the current active submission for the same assignment and student
        old = db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id, active=True)
        if old:
            old.update({'active': False})
        
        # Activate the specified submission
        db.session.query(Submission).filter_by(id=submission_id).update({'active': True})
        db.session.commit()
        
        return jsonify({"message": "Submission activated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@submission.route('/test_autograder_submission', methods=["POST"])
@cross_origin()
def test_autograder_submission():
    if "submission_file" not in request.files or "autograder_zip" not in request.files:
        raise BadRequestError("Missing required files: submission_file and autograder_zip")

    submission_file = request.files["submission_file"]
    autograder_zip = request.files["autograder_zip"]

    if not submission_file.filename or not autograder_zip.filename:
        raise BadRequestError("Invalid filenames")

    temp_id = str(uuid.uuid4())
    current_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(current_dir, 'temp_autograder', temp_id)
    os.makedirs(temp_dir, exist_ok=True)

    # Save files
    submission_path = os.path.join(temp_dir, secure_filename(submission_file.filename))
    autograder_path = os.path.join(temp_dir, secure_filename(autograder_zip.filename))
    submission_file.save(submission_path)
    autograder_zip.save(autograder_path)

    # Write Dockerfile
    dockerfile_content = f"""
    FROM python:3.9-slim
    RUN apt-get update && apt-get install -y --no-install-recommends python3-pip python3-dev unzip && rm -rf /var/lib/apt/lists/*
    COPY {os.path.basename(autograder_path)} /autograder/
    RUN unzip /autograder/{os.path.basename(autograder_path)} -d /autograder/source && \
        chmod +x /autograder/source/setup.sh && /autograder/source/setup.sh && \
        chmod +x /autograder/source/run_autograder && \
        mkdir -p /autograder/results /autograder/submission
    WORKDIR /autograder
    CMD ["/bin/bash", "/autograder/source/run_autograder"]
    """
    with open(os.path.join(temp_dir, 'Dockerfile'), 'w') as f:
        f.write(dockerfile_content)

    image_tag = f"test-autograder:{temp_id}"

    try:
        # Build image
        docker_client.images.build(path=temp_dir, tag=image_tag)

        # Start container
        container = docker_client.containers.run(
            image_tag, detach=True, tty=True, command="tail -f /dev/null"
        )

        # Copy submission
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            tar.add(submission_path, arcname=os.path.basename(submission_path))
        tar_stream.seek(0)
        container.put_archive("/autograder/submission/", tar_stream)

        # Run grading
        exec_proc = container.exec_run("/bin/bash /autograder/source/run_autograder")

        if exec_proc.exit_code != 0:
            raise InternalProcessingError("Autograder run failed")

        # Get results
        cat_result = container.exec_run("cat /autograder/results/results.json")
        if cat_result.exit_code != 0:
            raise InternalProcessingError("Failed to retrieve results.json")

        result_data = cat_result.output.decode()
        result_json = json.loads(result_data)

    finally:
        # Cleanup container and image
        try:
            if 'container' in locals():
                container.stop()
                container.remove()
            docker_client.images.remove(image=image_tag, force=True)
        except Exception as cleanup_err:
            print(f"Cleanup error: {cleanup_err}")

        # Remove temp dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    return jsonify({
        "message": "Dry run successful",
        "results": result_json,
        "score": result_json.get("score"),
        "active": result_json.get("active")
    }), 200
