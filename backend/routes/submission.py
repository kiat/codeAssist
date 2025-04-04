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
from flask import Blueprint, request, jsonify, flash, current_app
from flask_cors import cross_origin
from api import db
from api.models import Assignment, Submission, User, Course, Enrollment, TestCaseResult, TestCase
from api.schemas import AssignmentSchema, SubmissionSchema, UserSchema, EnrollmentSchema
from util.errors import BadRequestError, InternalProcessingError, ConflictError, NotFoundError, ForbiddenError, ServerTimeoutError
from datetime import datetime, timezone
import subprocess
import os
import hashlib
import docker 
import zipfile
import shutil
import time
from dotenv import load_dotenv
from openai import OpenAI
import threading
from sqlalchemy.orm import aliased
from sqlalchemy import desc, func


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


# Define a background task for obtaining and recording AI feedback.
def async_get_ai_feedback(app, submission_id, file_path, results_json_content):
    ctx = app.app_context()
    ctx.push()
    try:
        # Read the submitted code as text
        with open(file_path, 'r') as code_file:
            code_text = code_file.read()

        # alias for clarity
        assignment_alias = aliased(Assignment)
        course_alias = aliased(Course)
        student_alias = aliased(User)

        # query records for submission, assignment, course, and student that relate to this submission
        result = (
            db.session.query(Submission, assignment_alias, course_alias, student_alias)
            .join(assignment_alias, Submission.assignment_id == assignment_alias.id)
            .join(course_alias, assignment_alias.course_id == course_alias.id)
            .join(student_alias, Submission.student_id == student_alias.id)
            .filter(Submission.id == submission_id)
            .first()
        )

        if result:
            submission_record, assignment_record, course_record, student_profile = result

        if not assignment_record.ai_feedback_enabled:
            print(f"AI_FEEDBACK: Disabled for submission {submission_id}")
            ctx.pop()
            return

        student_insights = student_profile.coding_insights
        print("Initial Student Insights:", student_insights)

        # Prepare the prompt including both the code and autograder results.
        prompt_message = (
            f"{assignment_record.ai_feedback_prompt}"
            "Pay special attention to the past insights of this student:\n"
            f"{student_insights}"

            "Response should be strictly JSON, with no extra formatting, in the form:" \
            "{ 'insights': <concise array of bullet points which describe the overall deficiencies in this student's coding behavior across assignments>",
                "'annotations': [{'pattern': <> , 'comment': <>}, ...]"
            "}"
            "Code:\n\n"
            f"{code_text}\n\n"
            "Autograder results:\n\n"
            f"{results_json_content}\n\n"
        )


        # Use the new OpenAI API interface.
        # Pull api key from course record
        client = OpenAI(api_key=course_record.openai_api_key)

        # helper to format message properly depending on model
        def format_message(text, model="gpt-4o"):
            if "gpt-4o" in model:
                return [{ "type": "text", "text": str(text) }]
            return text
        
        SELECTED_MODEL = assignment_record.ai_feedback_model
        SELECTED_TEMPERATURE = assignment_record.ai_feedback_temperature

        print(SELECTED_MODEL, SELECTED_TEMPERATURE, assignment_record.ai_feedback_prompt, student_profile.coding_insights)
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": format_message("You are an AI that provides constructive criticism on submitted code."
                                              , SELECTED_MODEL)
                },
                {
                    "role": "user", 
                    "content": format_message(prompt_message, SELECTED_MODEL)
                }
            ],
            model=SELECTED_MODEL,
            max_tokens=700,
            temperature=SELECTED_TEMPERATURE,
        )

        # Extract the AI feedback text from the response.
        ai_feedback_text = response.choices[0].message.content

        # Clean up markdown-style formatting
        cleaned_text = ai_feedback_text.strip()

        # Remove surrounding ```json or ``` if present
        if cleaned_text.startswith("```"):
            lines = cleaned_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        # Unescape literal newlines
        cleaned_text = cleaned_text.replace("\\n", "\n")

        try:
            ai_feedback_json = json.loads(cleaned_text)

            if isinstance(ai_feedback_json, str):
                ai_feedback_json = json.loads(ai_feedback_json)
            
            # update student insights with new insights
            student_insights = ai_feedback_json["insights"]
            
            print("AI_FEEDBACK:")
            print(json.dumps(ai_feedback_json, indent=4))
            print("Student insights:")
            print(student_insights)
        except Exception as parse_error:
            print("AI_FEEDBACK: AI FEEDBACK FAILED")

            ai_feedback_json = {
                "error": "Failed to parse OpenAI response as JSON",
                "response_text": cleaned_text
            }
            print(ai_feedback_json)
    except Exception as openai_error:
        ai_feedback_json = {"error": f"Failed to get AI feedback: {str(openai_error)}"}
        print("AI_FEEDBACK: Error in AI Feedback:")
        print(str(openai_error))

    # Update the submission record in the DB with the AI feedback.
    submission_record = Submission.query.get(submission_id)
    submission_record.ai_feedback = json.dumps(ai_feedback_json)
    student_profile.coding_insights = str(student_insights)
    db.session.commit()

    ctx.pop()


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
    submissions_dir = os.path.join(assignment_dir, "submission")
    results_dir = os.path.join(assignment_dir, student_id, 'results')
    for directory in [submissions_dir, results_dir]:
        os.makedirs(directory, exist_ok=True)
    
    # Clean out old submission files in submissions_dir
    for filenames in os.listdir(submissions_dir):
        file_path_del = os.path.join(submissions_dir, filenames)
        try:
            if os.path.isfile(file_path_del) or os.path.islink(file_path_del):
                os.unlink(file_path_del)
            elif os.path.isdir(file_path_del):
                shutil.rmtree(file_path_del)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
            raise InternalProcessingError("Failed to grade submission")
    file_path = os.path.join(submissions_dir, filename)
    file.save(file_path)

    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    container = docker_client.containers.get(assignment.container_id)
    container.start()

    # copy the file into the correct place
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        tar.add(file_path, arcname=filename)
    tar_stream.seek(0)
    container.put_archive("/autograder/submission/", tar_stream)

    # run autograder
    try:
        # docker sdk exec function doesn't have timeout feature, so let's use subprocess for this
        exec_proc = subprocess.run(
            f"docker exec {assignment.container_id} /bin/bash /autograder/source/run_autograder".split(), 
            capture_output=True, 
            timeout=assignment.autograder_timeout)
    except subprocess.TimeoutExpired:
        container.stop()
        os.chdir(current_dir)
        raise ServerTimeoutError("Submitted program took too long to run")

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
    host_results_json_path = os.path.join(results_dir, 'results.json')
    with open(host_results_json_path, 'w') as file_obj:
        file_obj.write(results_json_content)

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
        active=True,
        completed=True,
        submission_number=submission_count + 1,
        ai_feedback=None  # Initially no AI feedback
    )
    db.session.add(new_submission)
    db.session.commit()

    # Clean up container
    container.exec_run(f"rm -rf /autograder/submission/{filename}")
    container.exec_run(f"rm -f /autograder/source/{filename}")

    container.stop()
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
    # Validate input file and parameters
    if "file" not in request.files:
        return BadRequestError("No file part")
    file = request.files["file"]
    assignment_id = request.form.get("assignment_id")
    autograder_timeout = request.form.get("autograder_timeout")
    if not assignment_id or not file.filename:
        raise BadRequestError("Missing required fields")

    # Set up paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assignment_dir = os.path.join(current_dir, 'upload_autograder', 'runs', assignment_id)
    os.makedirs(assignment_dir, exist_ok=True)

    # remove old zips if they exist   
    for filenames in os.listdir(assignment_dir):
        file_path = os.path.join(assignment_dir, filenames)
        if filenames.endswith(".zip"):
            os.remove(file_path)
    # Save the uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(assignment_dir, filename)
    file.save(filepath)

    # Query the database for the assignment
    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404
    
    # If the assignment already has an associated container, update it.
    if assignment.container_id:
        container_id = assignment.container_id

        try:
            container = docker_client.containers.get(container_id)
            container.start()

            # Remove old zip file from Docker container
            exit_code, output = container.exec_run("find /autograder -type f -name '*.zip' -delete")
            if exit_code != 0:
                print("Failed to remove old zip files: ", output.decode())
                raise InternalProcessingError("Failed to upload assignment autograder")
            
            # Remove old source files from Docker container
            exit_code, output = container.exec_run("rm -rf /autograder/source/")
            if exit_code != 0:
                print("Failed to remove old source files: ", output.decode())
                raise InternalProcessingError("Failed to upload assignment autograder")


            # Copy new files into Docker container. Docker's "put_archive" expects a tar
            # create tar archive
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                tar.add(file_path, arcname=file_path.split("/")[-1])
            tar_stream.seek(0)

            # copy tar archive into container
            success = container.put_archive("/autograder/", tar_stream.read())
            if not success:
                print("Failed to copy new files into docker container")
                raise InternalProcessingError("Failed to upload assignment autograder")


            # Unzip the uploaded file into /autograder/source/ in the Docker container
            exit_code, output = container.exec_run(f"unzip /autograder/{filename} -d /autograder/source")
            if exit_code != 0:
                print("Failed to unzip uploaded file in Docker container: ", output.decode())
                raise InternalProcessingError("Failed to upload assignment autograder")

            container.stop()
            return jsonify({"message": "Autograder uploaded and Docker image generated successfully", "image_name": f"autograder-{assignment_id}"}), 200
        except docker.errors.NotFound:
            print("Container with specified container id was not found.")
            raise NotFoundError("Failed to upload assignment autograder")
        except Exception as e:
            print("Unexpected error occurred when updating autograder container. ", str(e))
            raise InternalProcessingError("Failed to upload assignment autograder")

    # Write the Dockerfile
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
    with open(os.path.join(assignment_dir, 'Dockerfile'), 'w') as dockerfile:
        dockerfile.write(dockerfile_content)

    # Build Docker image
    try:
        image_name = f"autograder-{assignment_id}"
        docker_client.images.build(path=assignment_dir, tag=image_name)
    except docker.errors.BuildError as e:
        print("Error occurred when building new image. ", str(e))
        raise InternalProcessingError("Failed to upload assignment autograder")

    # Run Docker container
    container_name = f"ag_{assignment_id}"
    try:
        container = docker_client.containers.run(
            image_name, 
            name=container_name, 
            detach=True, 
            tty=True, 
            command="tail -f /dev/null"
        )
        container.stop()
    except docker.errors.ContainerError as e:
        print("Error occurred when running new container. ", str(e))
        raise InternalProcessingError("Failed to upload assignment autograder")

    # Update the assignment record with the new container ID and autograder timeout
    assignment.container_id = container_name
    assignment.autograder_timeout = autograder_timeout
    db.session.commit()

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
    submission_to_delete = Submission.query.get(submission_id)

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
        return jsonify({"error": "not sufficient details"})
    
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
