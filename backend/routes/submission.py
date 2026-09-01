import uuid
import json
import sys
import io
import statistics
import csv
import tarfile
import zipfile
import subprocess
import os
import docker
import shutil
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from functools import reduce
from flask import Blueprint, request, jsonify, current_app, session, send_file
from api import db
from api.models import Assignment, Submission, User, Course, Enrollment, TestCaseResult, TestCase, SubmissionSubmitter
from api.schemas import AssignmentSchema, SubmissionSchema, UserSchema, EnrollmentSchema
from util.errors import BadRequestError, InternalProcessingError, ConflictError, NotFoundError, ForbiddenError, ServerTimeoutError, SubmissionTimeoutError
from util.auth import get_user_course_role, require_authenticated, require_course_role
from datetime import datetime, timezone
from sqlalchemy import desc, func
from ai_feedback.integration import async_get_ai_feedback
import threading


submission = Blueprint('submission', __name__)
_docker_client = None

def get_docker_client():
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client

ALLOWED_EXTENSIONS = {'py','zip'}

def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _stored_file_to_bytes(value):
    if value is None:
        return None
    if isinstance(value, memoryview):
        return value.tobytes()
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    return bytes(value)


def _json_from_stored_value(value):
    raw_value = _stored_file_to_bytes(value)
    if not raw_value:
        return None
    try:
        return json.loads(raw_value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _json_or_text_from_stored_value(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value

    raw_value = _stored_file_to_bytes(value)
    if raw_value is None:
        return None

    text_value = raw_value.decode("utf-8", errors="replace")
    try:
        return json.loads(text_value)
    except json.JSONDecodeError:
        return text_value


def _verify_course_staff(assignment_id):
    """Verify the requester is course staff (instructor/TA) for the given assignment.
    Returns the authenticated user id.
    Raises ForbiddenError if not authorized.
    """
    session_user_id = session.get("user_id")
    if not session_user_id:
        raise ForbiddenError("Not authenticated. Please log in.")
    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise NotFoundError("Assignment not found")
    course = db.session.query(Course).filter_by(id=assignment.course_id).first()
    if not course:
        raise NotFoundError("Course not found")
    if str(course.instructor_id) == str(session_user_id):
        return session_user_id
    enrollment = db.session.query(Enrollment).filter_by(
        course_id=assignment.course_id,
        student_id=session_user_id
    ).first()
    if enrollment and str(enrollment.role).lower() in {"instructor", "ta"}:
        return session_user_id
    raise ForbiddenError("Only course staff can perform this action")


def _verify_student_owner(student_id, assignment_id=None):
    """Verify the authenticated session matches the requested student_id,
    OR the requester is course staff (instructor/TA) for the assignment's course.
    
    This allows:
    - Students to access their own submissions
    - Instructors and TAs to access student submissions for grading/regrade requests
    
    If assignment_id is provided, checks course staff permissions.
    Otherwise, only allows the student themselves.
    """
    if not student_id:
        raise BadRequestError("Missing student_id")
    session_user_id = session.get("user_id")
    if not session_user_id:
        raise ForbiddenError("Not authenticated. Please log in.")
    
    # If the user is the student themselves, allow access
    if session_user_id == student_id:
        user = db.session.query(User).filter_by(id=student_id).first()
        if not user:
            raise NotFoundError("User not found")
        return user
    
    # If assignment_id is provided, check if the requester is course staff
    if assignment_id:
        assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
        if not assignment:
            raise NotFoundError("Assignment not found")
        
        course = db.session.query(Course).filter_by(id=assignment.course_id).first()
        if not course:
            raise NotFoundError("Course not found")
        
        # Check if requester is the course instructor
        if str(course.instructor_id) == str(session_user_id):
            user = db.session.query(User).filter_by(id=student_id).first()
            if not user:
                raise NotFoundError("User not found")
            return user
        
        # Check if requester is enrolled as instructor or TA in the course
        enrollment = db.session.query(Enrollment).filter_by(
            course_id=assignment.course_id,
            student_id=session_user_id
        ).first()
        
        if enrollment and str(enrollment.role).lower() in {"instructor", "ta"}:
            user = db.session.query(User).filter_by(id=student_id).first()
            if not user:
                raise NotFoundError("User not found")
            return user
    
    # If we get here, the requester is not authorized
    raise ForbiddenError("You can only access your own data")

@submission.route('/get_submissions', methods=["GET"])
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
        raise BadRequestError("Missing student_id or assignment_id")

    _verify_student_owner(student_id, assignment_id)

    submissions = db.session.query(Submission).filter_by(
        student_id=student_id, 
        assignment_id=assignment_id
    ).all()  

    if not submissions:
        raise NotFoundError("No submissions found for the provided student and assignment")
    submission_schema = SubmissionSchema(many=True)
    result = submission_schema.dump(submissions)

    return jsonify(result)


    
@submission.route('/upload_submission', methods=["POST"])
def upload_submission():
    if "file" not in request.files:
        raise BadRequestError("No file part")
    file = request.files["file"]
    assignment_id = request.form.get("assignment_id")
    student_id = request.form.get("student_id")
    if not assignment_id or not student_id or not file.filename:
        raise BadRequestError("Missing required fields")

    # Note: We intentionally do NOT pass assignment_id here.
    # Instructors/TAs should not upload submissions on behalf of students.
    _verify_student_owner(student_id)

    from api.models import AssignmentExtension
    from datetime import datetime, timezone

    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise NotFoundError("Assignment not found")

    # Enforce submission method restriction
    if not assignment.allow_file_upload:
        raise BadRequestError("File uploads are not allowed for this assignment.")

    # Retreive any extension for this student
    extension = db.session.query(AssignmentExtension).filter_by(
        assignment_id=assignment_id,
        student_id=student_id
    ).first()

    # Determine applicable dates & use extension if it exists
    release_date = extension.release_date_extension if extension and extension.release_date_extension else assignment.published_date
    due_date = extension.due_date_extension if extension and extension.due_date_extension else assignment.due_date
    late_due_date = extension.late_due_date_extension if extension and extension.late_due_date_extension else assignment.late_due_date

    now = datetime.now(timezone.utc)

    # Assignment must be published
    if not assignment.published:
        raise BadRequestError("Assignment is not published yet.")

    # Must not be before release date
    if release_date and now < release_date:
        raise BadRequestError("Cannot submit before the release date.")

    # Must not be past due/late due window
    if due_date and now > due_date:
        if assignment.late_submission:
            if late_due_date and now > late_due_date:
                raise BadRequestError("Submission period has ended (past late due date).")
        else:
            raise BadRequestError("Submission period has ended (past due date).")


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
    container = get_docker_client().containers.run(
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
def upload_assignment_autograder():
    if "file" not in request.files:
        raise BadRequestError("No file part")
    file = request.files["file"]
    assignment_id = request.form.get("assignment_id")
    autograder_timeout = request.form.get("autograder_timeout")
    if not assignment_id or not file.filename:
        raise BadRequestError("Missing required fields")

    require_authenticated()

    assignment_for_auth = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment_for_auth:
        raise NotFoundError("Assignment not found")

    require_course_role(assignment_for_auth.course_id, {"instructor", "ta"}, "Only instructors or TAs can upload an autograder")

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
        raise NotFoundError("Assignment not found")

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
        get_docker_client().images.build(path=assignment_dir, tag=image_name)
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
    if not student:
        raise NotFoundError("User not found")

    student_id = student.id

    # Security: Verify the requester owns the data or is course staff
    _verify_student_owner(student_id, assignment_id)

    submission = (db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id)
                    .order_by(desc(Submission.submitted_at)).limit(1))
    submission = SubmissionSchema().dump(submission, many=True)
    
    return jsonify(submission)


@submission.route('/get_latest_submission', methods=["GET"])
def get_latest_submission():
    student_id = request.args.get("student_id")
    assignment_id = request.args.get("assignment_id")

    if not student_id or not assignment_id:
        raise BadRequestError("Missing student_id or assignment_id")

    _verify_student_owner(student_id, assignment_id)

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
def get_all_assignment_submissions():
    assignment_id = request.args.get("assignment_id")

    if not assignment_id:
        raise BadRequestError("Missing assignment_id")

    # Security: Verify the requester is course staff or admin
    _verify_course_staff(assignment_id)

    # Query for all submissions related to the assignment
    all_submissions = Submission.query.filter_by(
        assignment_id=assignment_id
    ).order_by(Submission.submitted_at.desc()).all()

    if not all_submissions:
        raise NotFoundError("No submissions found for this assignment")

    # Serialize the submission data
    submissions_schema = SubmissionSchema(many=True)  # Set 'many=True' to handle multiple objects
    submissions_data = submissions_schema.dump(all_submissions)

    return jsonify(submissions_data), 200


def _percentage_histogram(scores, max_points):
    """10 fixed-width buckets over [0, max_points]. Scores outside that
    range (extra credit above max_points, or a negative score, which
    Submission.score has no DB constraint against) get their own overflow/
    underflow bucket rather than being silently clamped into 0-10%/90-100%.
    """
    bucket_width = max_points / 10
    buckets = [0] * 10
    overflow = 0
    underflow = 0
    for s in scores:
        if s < 0:
            underflow += 1
            continue
        if s > max_points:
            overflow += 1
            continue
        # min(..., 9) so a score exactly equal to max_points lands in the
        # last bucket (90-100%) instead of a nonexistent 11th bucket. The
        # tiny epsilon guards against float division landing just under an
        # exact bucket boundary (e.g. 3.3 / 1.1 == 2.9999999999999996) and
        # misclassifying a boundary score into the bucket below it.
        idx = min(int(s / bucket_width + 1e-9), 9)
        buckets[idx] += 1

    histogram = [
        {
            "label": f"{i * 10}-{(i + 1) * 10}%",
            "bucket_start": round(i * bucket_width, 2),
            "bucket_end": round((i + 1) * bucket_width, 2),
            "count": buckets[i],
        }
        for i in range(10)
    ]
    if underflow:
        histogram.insert(0, {"label": "<0%", "bucket_start": None, "bucket_end": 0, "count": underflow})
    if overflow:
        histogram.append({"label": ">100%", "bucket_start": max_points, "bucket_end": None, "count": overflow})
    return histogram


def _raw_histogram(scores, score_min, score_max):
    """Fallback bucketing when the assignment has no autograder_points (or
    it's 0) to build percentage buckets against: 10 fixed-width buckets over
    the observed score range instead.
    """
    if score_min == score_max:
        # A single submission, or every graded score being identical, can't
        # be split into 10 non-degenerate buckets.
        return [{
            "label": f"{score_min:g}",
            "bucket_start": score_min,
            "bucket_end": score_min,
            "count": len(scores),
        }]

    bucket_width = (score_max - score_min) / 10
    buckets = [0] * 10
    for s in scores:
        idx = min(int((s - score_min) / bucket_width + 1e-9), 9)
        buckets[idx] += 1

    return [
        {
            "label": f"{score_min + i * bucket_width:.1f}-{score_min + (i + 1) * bucket_width:.1f}",
            "bucket_start": round(score_min + i * bucket_width, 2),
            "bucket_end": round(score_min + (i + 1) * bucket_width, 2),
            "count": buckets[i],
        }
        for i in range(10)
    ]


def _effective_max_points(active_submissions, assignment_max_points):
    """Assignment.autograder_points is a manually-entered field on the
    assignment and can drift from what the autograder actually grades out
    of (e.g. it's left at a default of 100 while the configured test suite
    only totals 20 points) -- so prefer the real total computed from a
    graded submission's own results.json (sum of each test's max_score,
    the same source of truth /export_evaluations reads from) over the
    configured field, falling back to it only when no submission has
    parseable results yet.
    """
    computed_max = 0
    for sub in active_submissions:
        raw = sub.results
        if isinstance(raw, memoryview):
            raw = raw.tobytes()
        if not raw:
            continue
        try:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            data = json.loads(raw)
            total = sum(t.get("max_score", 0) or 0 for t in data.get("tests", []) or [])
            if total > computed_max:
                computed_max = total
        except (ValueError, TypeError, AttributeError):
            continue
    return computed_max if computed_max > 0 else assignment_max_points


def _compute_grade_statistics(scores, max_points):
    count = len(scores)
    if count == 0:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "stdev": None,
            "max_points": max_points,
            "mode": "percentage" if (max_points and max_points > 0) else "raw",
            "histogram": [],
        }

    score_min = min(scores)
    score_max = max(scores)

    if max_points and max_points > 0:
        histogram = _percentage_histogram(scores, max_points)
        mode = "percentage"
    else:
        histogram = _raw_histogram(scores, score_min, score_max)
        mode = "raw"

    return {
        "count": count,
        "mean": round(statistics.mean(scores), 2),
        "median": round(statistics.median(scores), 2),
        "min": score_min,
        "max": score_max,
        # Population stdev, not sample stdev: `scores` is the entire set of
        # graded submissions for this assignment, not a sample drawn from a
        # larger population. Also defined for n == 1 (returns 0.0), which
        # avoids a separate low-n guard that statistics.stdev would need.
        "stdev": round(statistics.pstdev(scores), 2),
        "max_points": max_points,
        "mode": mode,
        "histogram": histogram,
    }


@submission.route('/get_grade_statistics', methods=["GET"])
def get_grade_statistics():
    '''
    /get_grade_statistics computes summary stats (mean, median, min, max,
    stdev) and a histogram of the score distribution for an assignment's
    graded submissions.
    @param assignment_id  the id of the assignment
    '''
    assignment_id = request.args.get("assignment_id")
    if not assignment_id:
        raise BadRequestError("Missing assignment_id")

    # Security: Verify the requester is course staff or admin
    _verify_course_staff(assignment_id)

    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise NotFoundError("Assignment not found")

    # Only the active submission counts per student, and only if it's been
    # graded (an active submission can still have score == None while
    # autograding/AI feedback is in progress).
    active_submissions = Submission.query.filter_by(
        assignment_id=assignment_id, active=True
    ).all()
    scores = [s.score for s in active_submissions if s.score is not None]
    max_points = _effective_max_points(active_submissions, assignment.autograder_points)

    stats = _compute_grade_statistics(scores, max_points)
    return jsonify(stats), 200


@submission.route('/export_evaluations', methods=["GET"])
def export_evaluations():
    '''
    /export_evaluations builds and streams a zip file containing one CSV per
    autograder test (keyed by each test's "name" in the submission's
    results.json), each listing every enrolled student's result for that
    test ("no submission" for students who never submitted).
    @param assignment_id  the id of the assignment
    '''
    assignment_id = request.args.get("assignment_id")
    if not assignment_id:
        raise BadRequestError("Missing assignment_id")

    # Security: Verify the requester is course staff or admin
    _verify_course_staff(assignment_id)

    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise NotFoundError("Assignment not found")

    # Full student roster for the course, not just students who submitted --
    # a student who never submitted has no Submission row at all, so basing
    # the export on submissions alone would silently drop them instead of
    # showing them as a "no submission" row.
    enrolled_students = (
        db.session.query(User)
        .join(Enrollment, Enrollment.student_id == User.id)
        .filter(
            Enrollment.course_id == assignment.course_id,
            func.lower(Enrollment.role) == "student",
        )
        .order_by(User.name.asc())
        .all()
    )

    active_submissions = Submission.query.filter_by(
        assignment_id=assignment_id, active=True
    ).order_by(Submission.submitted_at.asc()).all()
    submission_by_student = {sub.student_id: sub for sub in active_submissions}

    # Parse each submission's results.json (stored as a raw blob on
    # Submission.results) once, keyed by student id then test name, and
    # track the order test names first appear in so spreadsheets follow the
    # assignment's actual test order rather than an arbitrary one. Also
    # remember each test's "number" (e.g. "2.3"), if the autograder set one,
    # since test names are often full sentences/expressions (e.g. "Evaluate
    # 8 / 4 * 2") that lose their meaning once filename-sanitized.
    tests_by_student = {}
    test_name_order = []
    seen_names = set()
    number_by_name = {}
    for sub in active_submissions:
        tests_by_name = {}
        raw = sub.results
        if isinstance(raw, memoryview):
            raw = raw.tobytes()
        if raw:
            try:
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                data = json.loads(raw)
                for test in data.get("tests", []) or []:
                    name = test.get("name")
                    if not name:
                        continue
                    tests_by_name[name] = test
                    if name not in seen_names:
                        seen_names.add(name)
                        test_name_order.append(name)
                        number_by_name[name] = test.get("number")
            except (ValueError, TypeError, AttributeError):
                pass
        tests_by_student[sub.student_id] = tests_by_name

    zip_buffer = io.BytesIO()
    used_names = {}

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        if not test_name_order:
            zf.writestr(
                "README.txt",
                "No graded test results found for this assignment yet.\n",
            )
        for name in test_name_order:
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow([
                "question",
                "student_name",
                "student_email",
                "status",
                "score",
                "max_score",
                "output",
                "expected_output",
            ])
            for student in enrolled_students:
                if student.id not in submission_by_student:
                    writer.writerow([name, student.name, student.email_address, "no submission", "", "", "", ""])
                    continue
                test = tests_by_student.get(student.id, {}).get(name, {})
                writer.writerow([
                    name,
                    student.name,
                    student.email_address,
                    test.get("status", ""),
                    test.get("score", ""),
                    test.get("max_score", ""),
                    test.get("output", ""),
                    test.get("expected_output", ""),
                ])

            # Prefer the autograder's own question number for the filename
            # (e.g. "Question_2.3.csv") since test names are often full
            # sentences/expressions that don't survive filename-sanitizing
            # intact (e.g. "Evaluate 8 / 4 * 2" -> "Evaluate_8_4__2"). The
            # full name is still preserved as the "question" column above.
            number = number_by_name.get(name)
            if number:
                base_label = secure_filename(f"Question_{number}") or "question"
            else:
                base_label = secure_filename(name) or "question"
            count = used_names.get(base_label, 0)
            used_names[base_label] = count + 1
            file_name = f"{base_label}.csv" if count == 0 else f"{base_label}_{count}.csv"
            zf.writestr(file_name, csv_buffer.getvalue())

    zip_buffer.seek(0)
    download_name = f"{secure_filename(assignment.name or str(assignment_id))}_evaluations.zip"

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=download_name,
    )

@submission.route('/export_submissions', methods=["GET"])
def export_submissions():
    '''
    /export_submissions builds and streams a zip file containing every
    student's active (latest) submission code file for an assignment,
    plus a JSON metadata file per submission (score, execution_time,
    test case pass/fail breakdown, AI feedback text).
    @param assignment_id  the id of the assignment
    '''
    assignment_id = request.args.get("assignment_id")
    if not assignment_id:
        raise BadRequestError("Missing assignment_id")

    # Security: Verify the requester is course staff or admin
    _verify_course_staff(assignment_id)

    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise NotFoundError("Assignment not found")

    active_submissions = Submission.query.filter_by(
        assignment_id=assignment_id, active=True
    ).order_by(Submission.submitted_at.asc()).all()

    zip_buffer = io.BytesIO()
    used_names = {}

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        if not active_submissions:
            zf.writestr(
                "README.txt",
                "No active submissions found for this assignment yet.\n",
            )
        for sub in active_submissions:
            student = db.session.query(User).filter_by(id=sub.student_id).first()

            co_submitter_rows = db.session.query(SubmissionSubmitter).filter_by(
                submission_id=sub.id
            ).all()
            submitter_ids = {str(r.submitter_id) for r in co_submitter_rows}
            submitter_ids.add(str(sub.student_id))
            submitter_users = db.session.query(User).filter(
                User.id.in_(submitter_ids)
            ).all() if submitter_ids else []
            submitter_names = sorted(u.name for u in submitter_users) or (
                [student.name] if student else ["unknown_student"]
            )
            submitter_metadata = sorted(
                [
                    {
                        "id": str(u.id),
                        "name": u.name,
                        "email": u.email_address,
                        "sis_user_id": u.sis_user_id,
                    }
                    for u in submitter_users
                ],
                key=lambda u: u["name"] or "",
            )

            base_label = secure_filename(
                (student.sis_user_id if student else None) or str(sub.student_id)
            ) or str(sub.student_id)
            count = used_names.get(base_label, 0)
            used_names[base_label] = count + 1
            folder_name = base_label if count == 0 else f"{base_label}_{count}"

            code_bytes = _stored_file_to_bytes(sub.student_code_file)
            code_filename = secure_filename(sub.file_name or "submission")
            zf.writestr(f"{folder_name}/{code_filename}", code_bytes or b"")

            results_bytes = _stored_file_to_bytes(sub.results)
            autograder_results = _json_from_stored_value(sub.results)
            if results_bytes:
                zf.writestr(f"{folder_name}/results.json", results_bytes)

            test_case_rows = db.session.query(TestCaseResult, TestCase).join(
                TestCase, TestCaseResult.test_case_id == TestCase.id
            ).filter(TestCaseResult.submission_id == sub.id).all()

            metadata = {
                "submission_id": str(sub.id),
                "student_id": str(sub.student_id),
                "student_name": student.name if student else None,
                "student_email": student.email_address if student else None,
                "student_sis_user_id": student.sis_user_id if student else None,
                "group_submitters": submitter_names,
                "submitters": submitter_metadata,
                "file_name": sub.file_name,
                "submission_number": sub.submission_number,
                "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None,
                "score": sub.score,
                "execution_time": sub.execution_time,
                "completed": sub.completed,
                "ai_feedback": _json_or_text_from_stored_value(sub.ai_feedback),
                "autograder_results": autograder_results,
                "test_case_results": [
                    {
                        "test_case_name": tc.test_case_name,
                        "passed": result.passed,
                        "student_output": result.student_output,
                        "expected_output": tc.expected_output,
                    }
                    for result, tc in test_case_rows
                ],
            }
            zf.writestr(
                f"{folder_name}/metadata.json",
                json.dumps(metadata, indent=2, default=str),
            )

    zip_buffer.seek(0)
    download_name = f"{secure_filename(assignment.name or str(assignment_id))}_submissions.zip"

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=download_name,
    )

@submission.route('/export_grades_csv', methods=["GET"])
def export_grades_csv():
    assignment_id = request.args.get("assignment_id")
    if not assignment_id:
        raise BadRequestError("Missing assignment_id")

    # Security: Verify the requester is course staff or admin
    session_user_id = _verify_course_staff(assignment_id)

    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise NotFoundError("Assignment not found")

    all_submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
    subs_by_student = {}
    for sub in all_submissions:
        subs_by_student.setdefault(sub.student_id, []).append(sub)

    enrolled_users = db.session.query(User).join(
        Enrollment, Enrollment.student_id == User.id
    ).filter(Enrollment.course_id == assignment.course_id).all()
    # Matches the frontend's row set: everyone enrolled except the viewer.
    students = [u for u in enrolled_users if u.id != session_user_id]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["First & Last Name", "Email", "Score", "Graded", "Submitted At (UTC)"])

    for student in students:
        active_sub = next((s for s in subs_by_student.get(student.id, []) if s.active), None)
        writer.writerow([
            student.name,
            student.email_address,
            active_sub.score if active_sub and active_sub.score is not None else "",
            "Yes" if active_sub else "No",
            active_sub.submitted_at.isoformat() if active_sub and active_sub.submitted_at else "",
        ])

    filename = secure_filename(f"{assignment.name}_grades.csv")
    return current_app.response_class(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@submission.route('/delete_submission', methods=["DELETE"])
def delete_submission():
    submission_id = request.args.get("submission_id")

    if not submission_id:
        raise BadRequestError("Missing submission_id")

    require_authenticated()

    submission_to_delete = db.session.get(Submission, submission_id)

    if not submission_to_delete:
        raise NotFoundError("No submission found to delete")

    submission_assignment = db.session.get(Assignment, submission_to_delete.assignment_id)
    if not submission_assignment:
        raise NotFoundError("Assignment not found")

    require_course_role(submission_assignment.course_id, {"instructor"}, "Only instructors can delete submissions")

    try:
        db.session.delete(submission_to_delete)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise InternalProcessingError("Failed to delete submission")

    return jsonify({"message": "Submission successfully deleted"}), 200

@submission.route('/get_submission_details', methods=["GET"])
def get_submission_details():
    '''
    /get_student_by_id gets the submission details from the db
    Requires from the frontend a JSON containing:
    @param submission_id    the submission id
    '''
    id = request.args.get("submission_id")

    if not id:
        raise BadRequestError("Missing submission id")
    
    submission_to_get = db.session.query(Submission).filter_by(id=id).first()

    if not submission_to_get:
        raise NotFoundError("No submission found")

    # Security: Verify the requester owns the submission or is course staff
    _verify_student_owner(str(submission_to_get.student_id), str(submission_to_get.assignment_id))
    
    submission = SubmissionSchema().dump(submission_to_get)
    return jsonify(submission), 200


@submission.route('/rerun_submission_autograder', methods=["POST"])
def rerun_submission_autograder():
    data = request.json or {}
    submission_id = data.get("submission_id")

    if not submission_id:
        raise BadRequestError("Missing submission_id")

    submission_to_rerun = db.session.get(Submission, submission_id)
    if not submission_to_rerun:
        raise NotFoundError("No submission found")

    assignment = db.session.get(Assignment, submission_to_rerun.assignment_id)
    if not assignment:
        raise NotFoundError("Assignment not found")

    requester_id = require_authenticated()

    is_owner = str(submission_to_rerun.student_id) == str(requester_id)
    is_staff = get_user_course_role(requester_id, assignment.course_id) in {"instructor", "ta"}
    if not (is_owner or is_staff):
        raise ForbiddenError("Not authorized to rerun this submission")

    if (
        not assignment.autograder_image_name
        or not assignment.autograder_image_name.strip()
    ):
        raise BadRequestError("No autograder configured for this assignment")

    student_code = submission_to_rerun.student_code_file
    if isinstance(student_code, memoryview):
        student_code = student_code.tobytes()
    elif isinstance(student_code, str):
        student_code = student_code.encode()

    if not student_code:
        raise BadRequestError("Submission file is not available for rerun")

    filename = secure_filename(submission_to_rerun.file_name or "submission.py")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assignment_dir = os.path.join(
        current_dir,
        'upload_autograder',
        'runs',
        str(assignment.id),
    )
    rerun_uuid = uuid.uuid4().hex[:8]
    submissions_dir = os.path.join(assignment_dir, "submission", f"rerun_{rerun_uuid}")
    results_dir = os.path.join(
        assignment_dir,
        str(submission_to_rerun.student_id),
        'results',
    )

    os.makedirs(submissions_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    file_path = os.path.join(submissions_dir, filename)
    with open(file_path, "wb") as file:
        file.write(student_code)

    container = None
    timeout = assignment.autograder_timeout or 300
    temp_container_name = f"rerun_submission_{uuid.uuid4().hex[:8]}"

    try:
        container = get_docker_client().containers.run(
            image=assignment.autograder_image_name,
            name=temp_container_name,
            detach=True,
            tty=True,
            command="tail -f /dev/null",
        )

        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            tar.add(file_path, arcname=filename)
        tar_stream.seek(0)
        container.put_archive("/autograder/submission/", tar_stream)

        exec_proc = subprocess.run(
            f"docker exec {temp_container_name} /bin/bash /autograder/source/run_autograder".split(),
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        timeout_result = {
            "tests": [
                {
                    "name": "Submission Timeout",
                    "score": 0,
                    "max_score": 0,
                    "status": "failed",
                    "output": "The submission did not complete within the time limit.",
                }
            ],
            "leaderboard": [],
            "visibility": "visible",
            "execution_time": f"{timeout:.2f}",
            "score": 0,
        }
        submission_to_rerun.results = json.dumps(timeout_result).encode()
        submission_to_rerun.score = 0
        submission_to_rerun.execution_time = float(timeout)
        submission_to_rerun.completed = False
        submission_to_rerun.ai_feedback = None
        db.session.commit()
        if container:
            try:
                container.stop()
                container.remove()
            except Exception:
                pass
        raise SubmissionTimeoutError(
            "Submitted program took too long to run",
            submission_to_rerun.id,
        )
    except Exception:
        if container:
            try:
                container.stop()
                container.remove()
            except Exception:
                pass
        raise InternalProcessingError("Failed to rerun autograder")

    if exec_proc.returncode != 0:
        stderr = getattr(exec_proc, "stderr", b"") or getattr(exec_proc, "output", b"")
        print(f"Error: Autograder rerun failed, details: {stderr.decode(errors='ignore')}")
        if container:
            try:
                container.stop()
                container.remove()
            except Exception:
                pass
        raise InternalProcessingError("Failed to rerun autograder")

    cat_result = container.exec_run("cat /autograder/results/results.json")
    if cat_result.exit_code != 0:
        print(
            "Error: Failed to retrieve rerun results.json, details: "
            f"{cat_result.output.decode(errors='ignore')}"
        )
        if container:
            try:
                container.stop()
                container.remove()
            except Exception:
                pass
        raise InternalProcessingError("Failed to retrieve autograder results")

    results_json_content = cat_result.output.decode()
    if container:
        try:
            container.stop()
            container.remove()
        except Exception:
            pass

    try:
        parsed_results = json.loads(results_json_content)
    except json.JSONDecodeError:
        raise InternalProcessingError("Autograder returned invalid results JSON")

    host_results_json_path = os.path.join(results_dir, f'results_{rerun_uuid}.json')
    with open(host_results_json_path, 'w') as file:
        file.write(results_json_content)

    submission_to_rerun.results = results_json_content.encode()
    submission_to_rerun.score = parsed_results.get("score")
    try:
        submission_to_rerun.execution_time = float(
            parsed_results.get("execution_time", 0) or 0
        )
    except (TypeError, ValueError):
        submission_to_rerun.execution_time = 0
    submission_to_rerun.completed = True
    submission_to_rerun.ai_feedback = None
    db.session.commit()

    if getattr(assignment, "ai_feedback_enabled", False):
        app_obj = current_app._get_current_object()
        threading.Thread(
            target=async_get_ai_feedback,
            args=(app_obj, submission_to_rerun.id, file_path, results_json_content),
        ).start()

    return jsonify({
        "message": "Autograder rerun completed",
        "results_path": host_results_json_path,
        "submission": SubmissionSchema().dump(submission_to_rerun),
    }), 200


@submission.route('/get_active_submission', methods=["GET"])
def get_active_submission():
    '''

    '''
    student = request.args.get("student_id")
    assignment = request.args.get("assignment_id")

    if not assignment or not student:
      raise BadRequestError("not sufficient details")

    _verify_student_owner(student, assignment)

    submission = db.session.query(Submission).filter_by(assignment_id=assignment, student_id=student, active=True).first()

    if not submission:
        return jsonify({"message": "No active submission found", "data": None}), 200
    
    details = SubmissionSchema().dump(submission)

    return jsonify(details), 200


@submission.route('/activate_submission', methods=["POST"])
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
        raise BadRequestError("Missing submission_id, student_id, or assignment_id")

    _verify_student_owner(student_id, assignment_id)

    submission_to_activate = db.session.get(Submission, submission_id)
    if not submission_to_activate:
        raise NotFoundError("No submission found")
    if (
        str(submission_to_activate.student_id) != str(student_id)
        or str(submission_to_activate.assignment_id) != str(assignment_id)
    ):
        raise ForbiddenError("Submission does not belong to the given student and assignment")

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
        raise InternalProcessingError("Failed to activate submission")


@submission.route('/test_autograder_submission', methods=["POST"])
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
        get_docker_client().images.build(path=temp_dir, tag=image_tag)

        # Start container
        container = get_docker_client().containers.run(
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
            get_docker_client().images.remove(image=image_tag, force=True)
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
