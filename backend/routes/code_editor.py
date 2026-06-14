import uuid
import json
import os
import subprocess
import io
import tarfile
import threading
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from api import db
from api.models import CodeDraft, Assignment, Submission, User, AssignmentExtension, Course
from api.schemas import CodeDraftSchema, SubmissionSchema
from util.errors import BadRequestError, NotFoundError, InternalProcessingError, SubmissionTimeoutError
from openai import OpenAI
from util.encryption_utils import decrypt_api_key
from ai_integration import async_get_ai_feedback
import docker

code_editor = Blueprint('code_editor', __name__)
docker_client = docker.from_env()


@code_editor.route('/save_code_draft', methods=["POST"])
@cross_origin()
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

    if not student_id or not assignment_id or content is None:
        raise BadRequestError("Missing required fields: student_id, assignment_id, content")

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
@cross_origin()
def get_code_drafts():
    """
    Get all code drafts for a student/assignment (version history).
    Query params: student_id, assignment_id
    """
    student_id = request.args.get("student_id")
    assignment_id = request.args.get("assignment_id")

    if not student_id or not assignment_id:
        raise BadRequestError("Missing student_id or assignment_id")

    drafts = (
        db.session.query(CodeDraft)
        .filter_by(student_id=student_id, assignment_id=assignment_id)
        .order_by(CodeDraft.version_number.desc())
        .all()
    )

    return jsonify(CodeDraftSchema().dump(drafts, many=True)), 200


@code_editor.route('/get_latest_draft', methods=["GET"])
@cross_origin()
def get_latest_draft():
    """
    Get the latest code draft for a student/assignment.
    Query params: student_id, assignment_id
    """
    student_id = request.args.get("student_id")
    assignment_id = request.args.get("assignment_id")

    if not student_id or not assignment_id:
        raise BadRequestError("Missing student_id or assignment_id")

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
@cross_origin()
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

    if not student_id or not assignment_id or content is None:
        raise BadRequestError("Missing required fields: student_id, assignment_id, content")

    if len(content) > 100000:
        raise BadRequestError("Code content exceeds maximum length of 100KB")

    # Check assignment exists and is published
    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise NotFoundError("Assignment not found")

    if not assignment.published:
        raise BadRequestError("Assignment is not published yet.")

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
    container = docker_client.containers.run(
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


@code_editor.route('/ai_chat', methods=["POST"])
@cross_origin()
def ai_chat():
    """
    Chat with AI about the current code.
    Expects JSON: { student_id, assignment_id, message, code }
    Returns: { reply: "..." }
    """
    data = request.json
    student_id = data.get("student_id")
    assignment_id = data.get("assignment_id")
    user_message = data.get("message")
    code = data.get("code", "")

    if not student_id or not user_message:
        raise BadRequestError("Missing student_id or message")

    if not assignment_id:
        raise BadRequestError("Missing assignment_id")

    # Fetch assignment and course for API key
    assignment = db.session.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise NotFoundError("Assignment not found")
    if not assignment.ai_feedback_enabled:
        raise BadRequestError("AI chat is not enabled for this assignment.")

    course = db.session.query(Course).filter_by(id=assignment.course_id).first()
    if not course or not course.openai_api_key:
        raise BadRequestError("AI is not configured for this course. Please ask your instructor to set up an API key.")

    try:
        decrypted_api_key = decrypt_api_key(course.openai_api_key)
        client = OpenAI(api_key=decrypted_api_key)
    except Exception:
        raise InternalProcessingError("Failed to initialize AI client")

    VALID_MODELS = {"gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"}
    model = assignment.ai_feedback_model if assignment and assignment.ai_feedback_model else "gpt-4-turbo"
    if model not in VALID_MODELS:
        model = "gpt-4-turbo"
    temperature = assignment.ai_feedback_temperature if assignment and assignment.ai_feedback_temperature else 0.5

    system_prompt = (
        "You are an AI coding assistant for a programming course. "
        "Help students understand their code, debug issues, and improve their solutions. "
        "Do NOT provide the complete solution. Give hints, guiding questions, and explanations. "
        "Keep responses concise and encouraging."
    )

    user_prompt = f"Student's current code:\n```python\n{code}\n```\n\nStudent message: {user_message}"

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            max_tokens=500,
            temperature=float(temperature),
            timeout=30,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        error_msg = str(e)
        print(f"AI_CHAT error: {e}", flush=True)
        if "insufficient_quota" in error_msg or "429" in error_msg:
            raise BadRequestError("AI service quota exceeded. Please contact your instructor to update the API key.")
        elif "invalid_api_key" in error_msg or "401" in error_msg:
            raise BadRequestError("Invalid API key. Please contact your instructor.")
        elif "does not exist" in error_msg or "model_not_found" in error_msg:
            raise BadRequestError(f"AI model '{model}' is not available. Please contact your instructor.")
        raise InternalProcessingError(f"Failed to get AI response: {type(e).__name__}")

    return jsonify({"reply": reply}), 200
