import uuid
import json
import os
import subprocess
import io
import tarfile
import threading
import time
import logging
import requests
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app, session
from api import db
from api.models import CodeDraft, Assignment, Submission, User, AssignmentExtension, Course, Enrollment
from api.schemas import CodeDraftSchema, SubmissionSchema
from util.errors import BadRequestError, NotFoundError, InternalProcessingError, SubmissionTimeoutError, ForbiddenError, TooManyRequestsError
from util.url_utils import validate_ollama_url
from ai_feedback.integration import (
    async_get_ai_feedback,
    get_provider_and_model,
    get_provider_credentials,
    get_temperature,
    post_gemini_with_retry,
)
from ai_feedback.settings import (
    check_feedback_limits,
    get_enabled_feedback_prompt,
    record_feedback_request,
    get_student_feedback_status,
    get_chat_history,
    store_chat_message,
)
import docker

logger = logging.getLogger(__name__)

code_editor = Blueprint('code_editor', __name__)
_docker_client = None

# --- Rate limiting for run_code (per-user) ---
_run_code_timestamps = {}  # {student_id: [timestamps]}
_run_code_rate_lock = threading.Lock()
_RUN_CODE_RATE_LIMIT = 10  # max requests per user
_RUN_CODE_RATE_WINDOW = 60  # per 60 seconds


def _check_run_code_rate_limit(student_id):
    """Per-user sliding-window rate limiter for run_code (thread-safe)."""
    now = time.time()
    with _run_code_rate_lock:
        timestamps = _run_code_timestamps.get(student_id, [])
        # Prune timestamps outside the window
        while timestamps and timestamps[0] < now - _RUN_CODE_RATE_WINDOW:
            timestamps.pop(0)
        # Evict idle keys to prevent memory leak
        if not timestamps:
            _run_code_timestamps.pop(student_id, None)
            # Record this request as the first in the window
            _run_code_timestamps[student_id] = [now]
            return
        if len(timestamps) >= _RUN_CODE_RATE_LIMIT:
            raise TooManyRequestsError("Too many run requests. Please wait a moment and try again.")
        timestamps.append(now)


def _verify_student(student_id):
    """Verify that the authenticated session user matches the requested student_id.
    Checks session first (cheap, no DB), then queries the DB only if authenticated.
    This avoids leaking which UUIDs exist via different error messages."""
    if not student_id:
        raise BadRequestError("Missing student_id")
    # Check session FIRST — avoids leaking valid UUIDs to unauthenticated callers
    session_user_id = session.get("user_id")
    if not session_user_id:
        raise ForbiddenError("Not authenticated. Please log in.")
    if session_user_id != student_id:
        raise ForbiddenError("You can only access your own data")
    # Session matches — now verify the user actually exists in the database
    user = db.session.query(User).filter_by(id=student_id).first()
    if not user:
        raise NotFoundError("User not found")
    return user


def _verify_enrollment(student_id, course_id):
    """Verify that a student is enrolled in the given course. Raises 403 if not."""
    enrollment = db.session.query(Enrollment).filter_by(
        student_id=student_id, course_id=course_id
    ).first()
    if not enrollment:
        raise ForbiddenError("You are not enrolled in this course")
    return enrollment

def get_docker_client():
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client


@code_editor.route('/save_code_draft', methods=["POST"])
def save_code_draft():
    """
    Save a code draft (auto-save or manual save).
    Expects JSON: { student_id, assignment_id, content, file_name?, auto_saved? }
    """
    data = request.json
    student_id = data.get("student_id")
    assignment_id = data.get("assignment_id")
    content = data.get("content")
    file_name = data.get("file_name", "solution.py")
    auto_saved = data.get("auto_saved", False)

    _verify_student(student_id)

    if not assignment_id or content is None:
        raise BadRequestError("Missing required fields: assignment_id, content")

    if len(content) > 100000:
        raise BadRequestError("Code content exceeds maximum length of 100KB")

    # Find the latest version number for this student/assignment
    latest = (
        db.session.query(CodeDraft)
        .filter_by(student_id=student_id, assignment_id=assignment_id)
        .order_by(CodeDraft.version_number.desc())
        .first()
    )
    version_number = (latest.version_number + 1) if latest else 1

    draft = CodeDraft(
        id=str(uuid.uuid4()),
        student_id=student_id,
        assignment_id=assignment_id,
        content=content,
        file_name=file_name,
        version_number=version_number,
        saved_at=datetime.now(timezone.utc),
        auto_saved=auto_saved,
    )

    db.session.add(draft)
    db.session.commit()

    return jsonify(CodeDraftSchema().dump(draft)), 201


@code_editor.route('/get_code_drafts', methods=["GET"])
def get_code_drafts():
    """
    Get code drafts for a student/assignment.
    Query params: student_id, assignment_id, condensed (optional, default false)
    When condensed=true, returns only manual saves + the latest auto-save
    (skips intermediate auto-saves to keep history compact).
    """
    student_id = request.args.get("student_id")
    assignment_id = request.args.get("assignment_id")
    condensed = request.args.get("condensed", "false").lower() == "true"

    _verify_student(student_id)

    if not assignment_id:
        raise BadRequestError("Missing assignment_id")

    drafts = (
        db.session.query(CodeDraft)
        .filter_by(student_id=student_id, assignment_id=assignment_id)
        .order_by(CodeDraft.version_number.desc())
        .all()
    )

    if condensed:
        # Keep all manual saves + only the latest auto-save
        filtered = []
        latest_auto = None
        for d in drafts:
            if not d.auto_saved:
                filtered.append(d)
            elif latest_auto is None:
                latest_auto = d
        if latest_auto:
            filtered.append(latest_auto)
        drafts = sorted(filtered, key=lambda d: d.version_number, reverse=True)

    return jsonify(CodeDraftSchema().dump(drafts, many=True)), 200


@code_editor.route('/get_latest_draft', methods=["GET"])
def get_latest_draft():
    """
    Get the latest code draft for a student/assignment.
    Query params: student_id, assignment_id
    """
    student_id = request.args.get("student_id")
    assignment_id = request.args.get("assignment_id")

    _verify_student(student_id)

    if not assignment_id:
        raise BadRequestError("Missing assignment_id")

    draft = (
        db.session.query(CodeDraft)
        .filter_by(student_id=student_id, assignment_id=assignment_id)
        .order_by(CodeDraft.version_number.desc())
        .first()
    )

    if not draft:
        return jsonify({"message": "No drafts found", "data": None}), 200

    return jsonify(CodeDraftSchema().dump(draft)), 200


@code_editor.route('/submit_code', methods=["POST"])
def submit_code():
    """
    Submit code directly from the code editor (no file upload needed).
    Expects JSON: { student_id, assignment_id, content, file_name? }
    Runs autograder if available, saves submission, triggers AI feedback.
    """
    data = request.json
    student_id = data.get("student_id")
    assignment_id = data.get("assignment_id")
    content = data.get("content")
    file_name = data.get("file_name", "solution.py")

    _verify_student(student_id)

    if not assignment_id or content is None:
        raise BadRequestError("Missing required fields: assignment_id, content")

    if len(content) > 100000:
        raise BadRequestError("Code content exceeds maximum length of 100KB")

    # Check assignment exists and is published
    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise NotFoundError("Assignment not found")

    # Enforce submission method restriction
    if not assignment.enable_code_editor:
        raise BadRequestError("Code editor submissions are not allowed for this assignment.")

    if not assignment.published:
        raise BadRequestError("Assignment is not published yet.")

    # Enforce enable_code_editor server-side
    if not assignment.enable_code_editor:
        raise BadRequestError("Code editor is not enabled for this assignment.")

    # Verify student is enrolled in the course
    _verify_enrollment(student_id, assignment.course_id)

    # Check due dates (same logic as upload_submission)
    extension = db.session.query(AssignmentExtension).filter_by(
        assignment_id=assignment_id, student_id=student_id
    ).first()

    release_date = extension.release_date_extension if extension and extension.release_date_extension else assignment.published_date
    due_date = extension.due_date_extension if extension and extension.due_date_extension else assignment.due_date
    late_due_date = extension.late_due_date_extension if extension and extension.late_due_date_extension else assignment.late_due_date

    now = datetime.now(timezone.utc)

    if release_date and now < release_date:
        raise BadRequestError("Cannot submit before the release date.")

    if due_date and now > due_date:
        if assignment.late_submission:
            if late_due_date and now > late_due_date:
                raise BadRequestError("Submission period has ended (past late due date).")
        else:
            raise BadRequestError("Submission period has ended (past due date).")

    # Save content to a temp file for autograder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assignment_dir = os.path.join(current_dir, 'upload_autograder', 'runs', assignment_id)
    submission_uuid = uuid.uuid4().hex[:8]
    submissions_dir = os.path.join(assignment_dir, "submission", submission_uuid)
    results_dir = os.path.join(assignment_dir, student_id, 'results')

    for directory in [submissions_dir, results_dir]:
        os.makedirs(directory, exist_ok=True)

    file_path = os.path.join(submissions_dir, file_name)
    with open(file_path, 'w') as f:
        f.write(content)

    # Check if autograder exists
    if not assignment.autograder_image_name or assignment.autograder_image_name.strip() == "":
        # No autograder — save submission directly
        submission_count = db.session.query(Submission).filter_by(
            student_id=student_id, assignment_id=assignment_id
        ).count()
        old = db.session.query(Submission).filter_by(
            student_id=student_id, assignment_id=assignment_id, active=True
        )
        if old:
            old.update({'active': False})

        new_submission = Submission(
            id=str(uuid.uuid4()),
            file_name=file_name,
            student_id=student_id,
            assignment_id=assignment_id,
            student_code_file=content.encode('utf-8'),
            results=None,
            score=None,
            execution_time=0.0,
            submitted_at=datetime.now(timezone.utc),
            active=True,
            completed=True,
            submission_number=submission_count + 1,
            ai_feedback=None,
        )
        db.session.add(new_submission)
        db.session.commit()

        # Save a final draft copy
        _save_final_draft(student_id, assignment_id, content, file_name)

        return jsonify({
            "message": "Code submitted. No autograder found.",
            "submissionID": str(new_submission.id),
        }), 200

    # Run autograder in Docker
    temp_container_name = f"submission_{uuid.uuid4().hex[:8]}"
    container = get_docker_client().containers.run(
        image=assignment.autograder_image_name,
        name=temp_container_name,
        detach=True,
        tty=True,
        command="tail -f /dev/null",
    )

    try:
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            tar.add(file_path, arcname=file_name)
        tar_stream.seek(0)
        container.put_archive("/autograder/submission/", tar_stream)

        exec_proc = subprocess.run(
            f"docker exec {temp_container_name} /bin/bash /autograder/source/run_autograder".split(),
            capture_output=True,
            timeout=assignment.autograder_timeout,
        )
    except subprocess.TimeoutExpired:
        # Ensure container cleanup on timeout
        try:
            container.stop()
            container.remove()
        except Exception:
            pass

        timeout_result = {
            "tests": [{
                "name": "Submission Timeout",
                "score": 0,
                "max_score": 0,
                "status": "failed",
                "output": "The submission did not complete within the time limit.",
            }],
            "leaderboard": [],
            "visibility": "visible",
            "execution_time": f"{assignment.autograder_timeout:.2f}",
            "score": 0,
        }

        submission_count = db.session.query(Submission).filter_by(
            student_id=student_id, assignment_id=assignment_id
        ).count()
        old = db.session.query(Submission).filter_by(
            student_id=student_id, assignment_id=assignment_id, active=True
        )
        if old:
            old.update({'active': False})

        failed_submission = Submission(
            id=str(uuid.uuid4()),
            file_name=file_name,
            student_id=student_id,
            assignment_id=assignment_id,
            student_code_file=content.encode('utf-8'),
            results=json.dumps(timeout_result).encode(),
            score=0,
            execution_time=float(assignment.autograder_timeout),
            submitted_at=datetime.now(timezone.utc),
            active=True,
            completed=False,
            submission_number=submission_count + 1,
            ai_feedback=None,
        )
        db.session.add(failed_submission)
        db.session.commit()

        raise SubmissionTimeoutError("Submitted program took too long to run", failed_submission.id)
    except Exception as e:
        # Ensure container cleanup on any unexpected error
        try:
            container.stop()
            container.remove()
        except Exception:
            pass
        raise
    else:
        if exec_proc.returncode != 0:
            try:
                container.stop()
                container.remove()
            except Exception:
                pass
            raise InternalProcessingError("Failed to grade submission")

    # Get results (container still running here — clean up in finally)
    try:
        cat_result = container.exec_run("cat /autograder/results/results.json")
        if cat_result.exit_code != 0:
            raise InternalProcessingError("Failed to retrieve results.json")

        results_json_content = cat_result.output.decode()
        submission_uuid2 = uuid.uuid4().hex[:8]
        host_results_json_path = os.path.join(results_dir, f'results_{submission_uuid2}.json')
        with open(host_results_json_path, 'w') as f:
            f.write(results_json_content)

        submission_count = db.session.query(Submission).filter_by(
            student_id=student_id, assignment_id=assignment_id
        ).count()
        old = db.session.query(Submission).filter_by(
            student_id=student_id, assignment_id=assignment_id, active=True
        )
        if old:
            old.update({'active': False})

        result_data = json.loads(results_json_content)
        new_submission = Submission(
            id=str(uuid.uuid4()),
            file_name=file_name,
            student_id=student_id,
            assignment_id=assignment_id,
            student_code_file=content.encode('utf-8'),
            results=open(host_results_json_path, 'rb').read(),
            score=result_data.get('score'),
            execution_time=float(result_data.get('execution_time', 0)),
            submitted_at=datetime.now(timezone.utc),
            active=True,
            completed=True,
            submission_number=submission_count + 1,
            ai_feedback=None,
        )
        db.session.add(new_submission)
        db.session.commit()

        # Launch async AI feedback
        app_obj = current_app._get_current_object()
        threading.Thread(
            target=async_get_ai_feedback,
            args=(app_obj, new_submission.id, file_path, results_json_content),
        ).start()

        # Save a final draft copy
        _save_final_draft(student_id, assignment_id, content, file_name)

        return jsonify({
            "message": "Code submitted and autograded successfully",
            "submissionID": str(new_submission.id),
        }), 200
    finally:
        try:
            container.stop()
            container.remove()
        except Exception:
            pass


def _save_final_draft(student_id, assignment_id, content, file_name):
    """Save a non-auto-saved draft snapshot when the student explicitly submits."""
    latest = (
        db.session.query(CodeDraft)
        .filter_by(student_id=student_id, assignment_id=assignment_id)
        .order_by(CodeDraft.version_number.desc())
        .first()
    )
    version_number = (latest.version_number + 1) if latest else 1

    draft = CodeDraft(
        id=str(uuid.uuid4()),
        student_id=student_id,
        assignment_id=assignment_id,
        content=content,
        file_name=file_name,
        version_number=version_number,
        saved_at=datetime.now(timezone.utc),
        auto_saved=False,
    )
    db.session.add(draft)
    db.session.commit()


# Default Python image used when no autograder is configured
_DEFAULT_PYTHON_IMAGE = "python:3.11-slim"

AI_CHAT_SYSTEM_PROMPT = (
    "You are an AI coding assistant for a programming course. "
    "Help students understand their code, debug issues, and improve their solutions. "
    "Do NOT provide the complete solution. Give hints, guiding questions, and explanations. "
    "Keep responses concise and encouraging."
)


def _run_code_in_container(image, content, file_name, timeout):
    """
    Run student code inside a Docker container and return
    (stdout_text, stderr_text, return_code).
    """
    run_uuid = uuid.uuid4().hex[:8]
    container_name = f"run_{run_uuid}"
    container = None

    try:
        container = get_docker_client().containers.run(
            image=image,
            name=container_name,
            detach=True,
            tty=True,
            command="tail -f /dev/null",
        )

        # Write code to a temp file on disk, then put it in the container
        tmp_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'upload_autograder', 'runs', f'_run_{run_uuid}',
        )
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.join(tmp_dir, file_name)
        with open(tmp_path, 'w') as f:
            f.write(content)

        # Create the /tmp/run/ directory inside the container first
        container.exec_run("mkdir -p /tmp/run/")

        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            tar.add(tmp_path, arcname=file_name)
        tar_stream.seek(0)
        container.put_archive("/tmp/run/", tar_stream)

        # Execute the Python file and capture stdout + stderr
        exec_proc = subprocess.run(
            [
                "docker", "exec", container_name,
                "python", f"/tmp/run/{file_name}",
            ],
            capture_output=True,
            timeout=timeout,
        )

        stdout_text = exec_proc.stdout.decode(errors="replace")
        stderr_text = exec_proc.stderr.decode(errors="replace")
        return stdout_text, stderr_text, exec_proc.returncode

    except subprocess.TimeoutExpired:
        return "", "Execution timed out", 1
    finally:
        if container:
            try:
                container.stop()
                container.remove()
            except Exception:
                pass


def _run_autograder_in_container(image, content, file_name, assignment_id, timeout):
    """
    Run the autograder Docker image and return the parsed results dict,
    or None on failure.
    """
    run_uuid = uuid.uuid4().hex[:8]
    container_name = f"run_{run_uuid}"
    container = None
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assignment_dir = os.path.join(current_dir, 'upload_autograder', 'runs', assignment_id)
    submissions_dir = os.path.join(assignment_dir, "run", run_uuid)
    os.makedirs(submissions_dir, exist_ok=True)
    file_path = os.path.join(submissions_dir, file_name)
    with open(file_path, 'w') as f:
        f.write(content)

    try:
        container = get_docker_client().containers.run(
            image=image,
            name=container_name,
            detach=True,
            tty=True,
            command="tail -f /dev/null",
        )

        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            tar.add(file_path, arcname=file_name)
        tar_stream.seek(0)
        container.put_archive("/autograder/submission/", tar_stream)

        exec_proc = subprocess.run(
            f"docker exec {container_name} /bin/bash /autograder/source/run_autograder".split(),
            capture_output=True,
            timeout=timeout,
        )

        if exec_proc.returncode != 0:
            return None

        cat_result = container.exec_run("cat /autograder/results/results.json")
        if cat_result.exit_code == 0:
            return json.loads(cat_result.output.decode())
        return None
    except subprocess.TimeoutExpired:
        return None
    finally:
        if container:
            try:
                container.stop()
                container.remove()
            except Exception:
                pass


def _get_ai_chat_reply(provider, api_key, client, user_prompt, model, temperature):
    if provider == "openai":
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": AI_CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            max_tokens=500,
            temperature=float(temperature),
            timeout=30,
        )
        return response.choices[0].message.content.strip()

    if provider == "gemini":
        response = post_gemini_with_retry(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": api_key},
            payload={
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": f"{AI_CHAT_SYSTEM_PROMPT}\n\n{user_prompt}",
                            }
                        ],
                    }
                ],
                "generationConfig": {
                    "temperature": float(temperature),
                    "maxOutputTokens": 700,
                },
            },
            timeout=30,
        )

        if response.status_code >= 400:
            raise ValueError(f"Gemini API error: {response.text}")

        data = response.json()
        candidate = data.get("candidates", [{}])[0]
        return "".join(
            part.get("text", "")
            for part in candidate.get("content", {}).get("parts", [])
            if not part.get("thought")
        ).strip()

    if provider == "claude":
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 500,
                "temperature": float(temperature),
                "system": AI_CHAT_SYSTEM_PROMPT,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
            },
            timeout=30,
        )

        if response.status_code >= 400:
            raise ValueError(f"Claude API error: {response.text}")

        data = response.json()
        content = data.get("content", [])
        if content and content[0].get("type") == "text":
            return content[0].get("text", "").strip()
        return ""

    if provider == "ollama":
        validate_ollama_url(api_key)
        response = requests.post(
            f"{api_key}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": AI_CHAT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "options": {
                    "temperature": float(temperature),
                },
                "stream": False,
            },
            timeout=60,
        )

        if response.status_code >= 400:
            raise ValueError(f"Ollama API error: {response.text}")

        return response.json().get("message", {}).get("content", "").strip()

    raise ValueError(f"Unsupported AI provider: {provider}")


@code_editor.route('/run_code', methods=["POST"])
def run_code():
    """
    Run code without creating a submission.
    Expects JSON: { student_id, assignment_id, content, file_name? }

    Always returns the program's stdout/stderr output.
    If an autograder Docker image is configured the code is also
    executed through the autograder and individual test results are
    included in the response.
    """
    data = request.json
    student_id = data.get("student_id")
    assignment_id = data.get("assignment_id")
    content = data.get("content")
    file_name = data.get("file_name", "solution.py")

    _verify_student(student_id)
    _check_run_code_rate_limit(student_id)

    if not assignment_id or content is None:
        raise BadRequestError("Missing required fields: assignment_id, content")

    if len(content) > 100000:
        raise BadRequestError("Code content exceeds maximum length of 100KB")

    # Check assignment exists and is published
    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise NotFoundError("Assignment not found")

    # Enforce submission method restriction
    if not assignment.enable_code_editor:
        raise BadRequestError("Code editor submissions are not allowed for this assignment.")

    if not assignment.published:
        raise BadRequestError("Assignment is not published yet.")

    # Enforce enable_code_editor server-side
    if not assignment.enable_code_editor:
        raise BadRequestError("Code editor is not enabled for this assignment.")

    # Verify student is enrolled in the course
    _verify_enrollment(student_id, assignment.course_id)

    # Check due dates (same logic as submit_code)
    extension = db.session.query(AssignmentExtension).filter_by(
        assignment_id=assignment_id, student_id=student_id
    ).first()

    release_date = extension.release_date_extension if extension and extension.release_date_extension else assignment.published_date
    due_date = extension.due_date_extension if extension and extension.due_date_extension else assignment.due_date
    late_due_date = extension.late_due_date_extension if extension and extension.late_due_date_extension else assignment.late_due_date

    now = datetime.now(timezone.utc)

    if release_date and now < release_date:
        raise BadRequestError("Cannot run code before the release date.")

    if due_date and now > due_date:
        if assignment.late_submission:
            if late_due_date and now > late_due_date:
                raise BadRequestError("Submission period has ended (past late due date).")
        else:
            raise BadRequestError("Submission period has ended (past due date).")

    has_autograder = (
        assignment.autograder_image_name
        and assignment.autograder_image_name.strip()
    )
    timeout = assignment.autograder_timeout or 30

    # ------------------------------------------------------------------
    # 1. Always run the student's code and capture stdout / stderr
    # ------------------------------------------------------------------
    run_image = (
        assignment.autograder_image_name if has_autograder
        else _DEFAULT_PYTHON_IMAGE
    )
    try:
        stdout_text, stderr_text, return_code = _run_code_in_container(
            run_image, content, file_name, timeout,
        )
    except Exception as e:
        # Log details server-side but return sanitized error to client
        logger.error(f"RUN_CODE error: {e}", exc_info=True)
        return jsonify({
            "output": "An error occurred while running your code. Please try again.",
            "programOutput": "",
            "passed": False,
            "score": 0,
            "tests": [],
        }), 200

    # Build the human-readable output string from stdout / stderr
    output_parts = []
    if stdout_text.strip():
        output_parts.append(stdout_text)
    if stderr_text.strip():
        output_parts.append("--- stderr ---\n" + stderr_text)
    program_output = "\n".join(output_parts).strip()
    if not program_output:
        program_output = "(no output)"

    # ------------------------------------------------------------------
    # 2. If an autograder is configured, also run it for test results
    # ------------------------------------------------------------------
    tests = []
    score = 0
    passed = return_code == 0

    if has_autograder:
        try:
            result_data = _run_autograder_in_container(
                assignment.autograder_image_name, content,
                file_name, assignment_id, timeout,
            )
        except Exception as e:
            print(f"RUN_CODE autograder error: {e}", flush=True)
            result_data = None

        if result_data is not None:
            tests = result_data.get("tests", [])
            score = result_data.get("score", 0)
            # Use autograder score to determine pass/fail when available
            passed = score > 0 or return_code == 0
            # If autograder produced its own output, append it
            ag_output = result_data.get("output", "")
            if ag_output and ag_output.strip():
                program_output += "\n\n--- autograder ---\n" + ag_output

    return jsonify({
        "output": program_output,
        "programOutput": program_output,
        "stdout": stdout_text,
        "stderr": stderr_text,
        "passed": passed,
        "score": score,
        "tests": tests,
    }), 200


@code_editor.route('/ai_chat', methods=["POST"])
def ai_chat():
    """
    Chat with AI about the current code.
    Expects JSON: { student_id, assignment_id, message, code, prompt_id? }
    Returns: { reply: "...", feedback_status: { remaining, wait_seconds } }
    """
    data = request.json
    student_id = data.get("student_id")
    assignment_id = data.get("assignment_id")
    user_message = data.get("message")
    code = data.get("code", "")
    prompt_id = data.get("prompt_id")

    _verify_student(student_id)

    if not user_message:
        raise BadRequestError("Missing message")

    if not assignment_id:
        raise BadRequestError("Missing assignment_id")

    # Fetch assignment and course for provider settings and credentials.
    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise NotFoundError("Assignment not found")
    if not assignment.ai_feedback_enabled:
        raise BadRequestError("AI chat is not enabled for this assignment.")

    # Verify student is enrolled in the course to prevent quota abuse
    _verify_enrollment(student_id, assignment.course_id)

    # Check feedback limits (max_requests + wait_seconds)
    limits = check_feedback_limits(assignment, student_id)
    if not limits["allowed"]:
        raise TooManyRequestsError(limits["message"])

    # Validate prompt_id if provided and resolve the instructor prompt for API context
    instructor_prompt_text = None
    if prompt_id:
        try:
            prompt_config = get_enabled_feedback_prompt(assignment, prompt_id)
            instructor_prompt_text = prompt_config['prompt']
        except ValueError as e:
            raise BadRequestError(str(e))

    course = db.session.query(Course).filter_by(id=assignment.course_id).first()
    if not course:
        raise BadRequestError("Course not found for this assignment.")

    user_prompt = f"Student's current code:\n```python\n{code}\n```\n\nStudent message: {user_message}"
    provider, model = get_provider_and_model(assignment, course)
    temperature = get_temperature(assignment, course)

    try:
        api_key, client = get_provider_credentials(provider, course, assignment)
    except ValueError as e:
        error_message = str(e)
        if error_message.startswith("Missing "):
            raise BadRequestError("AI is not configured for this course or assignment. Please ask your instructor to set up an API key.")
        raise BadRequestError(error_message)
    except Exception:
        raise InternalProcessingError("Failed to initialize AI client")
  
    try:
        reply = _get_ai_chat_reply(provider, api_key, client, user_prompt, model, temperature)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"AI_CHAT error: {e}", exc_info=True)
        if "insufficient_quota" in error_msg or "429" in error_msg:
            raise BadRequestError("AI service quota exceeded. Please contact your instructor to update the API key.")
        elif "invalid_api_key" in error_msg or "401" in error_msg:
            raise BadRequestError("Invalid API key. Please contact your instructor.")
        elif "does not exist" in error_msg or "model_not_found" in error_msg:
            raise BadRequestError(f"AI model '{model}' is not available. Please contact your instructor.")
        raise BadRequestError(str(e))
    except BadRequestError:
        raise
    except Exception as e:
        print(f"AI_CHAT error: {e}", flush=True)
        raise InternalProcessingError(f"Failed to get AI response: {type(e).__name__}")

    # Store messages for AI memory — store the raw user message only (without
    # the instructor prompt prepended) so chat history stays concise and avoids
    # redundant prompt text when loaded for subsequent requests.
    try:
        store_chat_message(student_id, assignment_id, "user", user_message, prompt_id)
        store_chat_message(student_id, assignment_id, "assistant", reply)
    except Exception as e:
        logger.warning(f"AI_CHAT: Failed to store chat message: {e}")

    # Record the feedback request (wrapped so a DB error doesn't 500 after a
    # successful AI reply has already been generated).
    try:
        record_feedback_request(student_id, assignment_id, prompt_id)
    except Exception as e:
        logger.warning(f"AI_CHAT: Failed to record feedback request: {e}")

    # Get updated status
    status = get_student_feedback_status(assignment, student_id)

    return jsonify({"reply": reply, "feedback_status": status}), 200


@code_editor.route('/ai_feedback_status', methods=["GET"])
def ai_feedback_status():
    """
    Get the student's current AI feedback request status for an assignment.
    Query params: student_id, assignment_id
    Returns: { remaining, wait_seconds, max_requests, total_requests }
    """
    student_id = request.args.get("student_id")
    assignment_id = request.args.get("assignment_id")

    _verify_student(student_id)

    if not assignment_id:
        raise BadRequestError("Missing assignment_id")

    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise NotFoundError("Assignment not found")

    if not assignment.ai_feedback_enabled:
        return jsonify({
            "remaining": 0,
            "wait_seconds": 0,
            "max_requests": 0,
            "total_requests": 0,
            "ai_feedback_enabled": False,
        }), 200

    _verify_enrollment(student_id, assignment.course_id)

    status = get_student_feedback_status(assignment, student_id)
    status["ai_feedback_enabled"] = True
    return jsonify(status), 200
