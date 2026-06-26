import uuid
import os
import csv
import requests
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from api import db
from api.models import (
    Assignment,
    Course,
    Enrollment,
    User,
    Submission,
    RegradeRequest,
)
from api.schemas import AssignmentSchema, CourseSchema, EnrollmentSchema, UserSchema
from util.errors import BadRequestError, InternalProcessingError, ConflictError, NotFoundError, ForbiddenError
from util.encryption_utils import encrypt_api_key, decrypt_api_key
from ai_feedback.integration import (
    CORRECTNESS_SYSTEM_PROMPT,
    get_gemini_generation_config,
    parse_feedback_json,
)
from openai import OpenAI

course = Blueprint("course", __name__)

ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_FOLDER = 'uploads'
SUPPORTED_AI_PROVIDERS = {"openai", "gemini", "claude", "ollama"}

def is_supported_openai_model(model_id):
    """
    Filter OpenAI models shown in the dropdown.

    Keep standard text chat models that work with this app's chat completion
    request shape. Remove o-series and special-purpose models that may appear
    in the models API but fail with max_tokens, response_format, or text-only
    chat completions.
    """
    normalized_model_id = (model_id or "").lower()
    blocked_prefixes = ("o1", "o3", "o4")
    blocked_keywords = [
        "audio",
        "dall-e",
        "embedding",
        "image",
        "instruct",
        "moderation",
        "preview",
        "realtime",
        "search",
        "transcribe",
        "tts",
        "whisper",
    ]

    if normalized_model_id.startswith(blocked_prefixes):
        return False

    if any(keyword in normalized_model_id for keyword in blocked_keywords):
        return False

    return normalized_model_id.startswith("gpt-")


def is_supported_gemini_model(model_id):
    """
    Filter Gemini models shown in the dropdown.

    Keep normal Gemini text generation models.
    Remove research, antigravity, embedding, audio, image, and other special models.
    """
    blocked_keywords = [
        "embedding",
        "aqa",
        "imagen",
        "veo",
        "tts",
        "native-audio",
        "live",
        "learnlm",
        "deep-research",
        "antigravity",
        "preview",
        "exp",
        "experimental",
    ]

    blocked_models = {
        "gemini-2.0-flash",
    }

    if model_id in blocked_models:
        return False

    if any(keyword in model_id.lower() for keyword in blocked_keywords):
        return False

    return model_id.startswith("gemini-")


def is_supported_claude_model(model_id):
    """
    Filter Claude models shown in the dropdown.

    Remove known unavailable or special-access Claude models.
    """
    blocked_keywords = [
        "fable",
        "mythos",
    ]

    if any(keyword in model_id.lower() for keyword in blocked_keywords):
        return False

    return model_id.startswith("claude-")

@course.route("/create_course", methods=["POST", "GET"])
@cross_origin()
def create_course():
    """
    /create_course creates a course in the database
    Requires from the frontend a JSON containing:
    @param name             name of the course
    @param instructor_id    class owner (instructor) of the course
    @param semester         semester of the course
    @param year             year of the course
    @param entryCode        entryCode of the course
    """
    data = request.json
    required_fields = ["name", "instructor_id", "semester", "year", "entryCode"]

    # validate request
    if not all(field in data and data[field] for field in required_fields):
        raise BadRequestError("Missing required fields")
    
    # set default value for allowEntryCode if not provided
    data["allowEntryCode"] = data.get("allowEntryCode", True)

    # check for duplicate entryCode
    if db.session.query(Course).filter_by(entryCode=data["entryCode"]).first():
        raise ConflictError("Course with the provided entry code already exists")

    course = Course(id = str(uuid.uuid4()), **data)

    enrollment = Enrollment(
        student_id=data["instructor_id"],
        course_id=course.id,
        role="instructor",
    )

    try:
        db.session.add(course)
        db.session.add(enrollment)
        db.session.commit()
        return jsonify(CourseSchema().dump(course)), 201
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Failed to create course")


@course.route("/enroll_course", methods=["POST"])
@cross_origin()
def enroll_course():
    """
    /enroll_course enrolls a student in a course using entryCode
    Requires from the frontend a JSON containing:
    @param entryCode        entryCode of the course
    @param user_id       id of the student
    """
    data = request.json
    required_fields = ["user_id", "entryCode"]

    # validate request
    if not all(field in data for field in required_fields):
        raise BadRequestError("Missing required fields")

    course = db.session.query(Course).filter_by(entryCode=data["entryCode"]).first()
    
    # Check if the course exists
    if not course:
        raise NotFoundError("Course with the provided entry code does not exist")
    
    # Check if student is already enrolled
    if db.session.query(Enrollment).filter_by(student_id=data["user_id"], course_id=course.id).first():
        raise ConflictError("User is already enrolled in this course")
    
    # returning same error message b/c user probably shouldn't know about hidden classes existing
    if course.allowEntryCode is False:
        raise ForbiddenError("Course with the provided entry code does not exist")

    enrollment = Enrollment(
        student_id=data["user_id"],
        course_id=course.id,
        role="student",
    )
    try:
        db.session.add(enrollment)
        db.session.commit()
        return jsonify(EnrollmentSchema().dump(enrollment)), 201
    except Exception as e:
        raise InternalProcessingError("Failed to enroll in course")
    
@course.route("/leave_course", methods=["POST"])
@cross_origin()
def leave_course():
    data = request.json
    user_id = data.get("user_id")
    course_id = data.get("course_id")

    if not user_id or not course_id:
        raise BadRequestError("Missing user_id or course_id")

    enrollment = db.session.query(Enrollment).filter_by(
        student_id=user_id,
        course_id=course_id
    ).first()

    if not enrollment:
        raise NotFoundError("Enrollment not found")

    if enrollment.role == "instructor":
        raise ForbiddenError("Instructors cannot leave their own course")

    try:
        db.session.delete(enrollment)
        db.session.commit()
        return jsonify({"message": "Left course successfully"}), 200
    except:
        db.session.rollback()
        raise InternalProcessingError("Failed to leave course")

@course.route("/update_course", methods=["PUT"])
@cross_origin()
def update_course():
    """
    /update_course updates a course in the database
    Requires from the frontend a JSON containing
    @param course_id        id of the course in database
    @param description      description of the course
    @param name             name of the course
    @param semester         semester of the course
    @param year             year of the course
    @param entryCode        entry code of the course
    @param allowEntryCode   whether entry code is allowed
    """
    data = request.json
    required_fields = ["course_id", "description", "name", "semester", "year", "entryCode", "allowEntryCode"]

    if not all(field in data for field in required_fields):
        raise BadRequestError("Missing required fields")
    
    # Check that updated entryCode is unique or already owned by the class
    existing_class = db.session.query(Course).filter_by(entryCode=data["entryCode"]).first()
    if existing_class and existing_class.id != data["course_id"]:
        raise ConflictError("Course with the provided entry code already exists")
    
    course_id = data["course_id"]    
    del data["course_id"]

    updated_course_info = {getattr(Course, name): val for name, val in data.items()}

    try:
        db.session.query(Course).filter_by(id=course_id).update(updated_course_info)
        db.session.commit()
        return jsonify({"message": "Course updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Failed to update course")


@course.route("/delete_course", methods=["DELETE"])
@cross_origin()
def delete_course():
    course_id = request.args.get("course_id")
    
    # Check for course_id
    if not course_id:
        raise BadRequestError("Missing required fields")
    
    course = db.session.query(Course).filter_by(id=course_id).first()
    
    if not course:
        raise NotFoundError("Course not found")

    # Check if there are any assignments for this course
    if db.session.query(Assignment).filter_by(course_id=course_id).first():
        raise ConflictError("Cannot delete course with assignments")

    try:
        # delete enrollments
        enrollments = db.session.query(Enrollment).filter_by(course_id=course_id).all()
        if enrollments:
            for enrollment in enrollments:
                db.session.delete(enrollment)
            db.session.commit()

        # delete course
        db.session.delete(course)
        db.session.commit()
        return jsonify({"message": "Course deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Failed to delete course")

@course.route("/delete_all_assignments", methods=["DELETE"])
@cross_origin()
def delete_all_assignments():
    course_id = request.args.get("course_id")
    if not course_id or course_id == "":
        raise BadRequestError("Missing course_id argument")

    # Check if there are any assignments for this course
    assignments = (db.session.query(Assignment).filter_by(course_id=course_id).all())

    if not assignments:
        raise NotFoundError("No assignments found for this course")
    
    assignment_ids = [a.id for a in assignments]

    try:
        db.session.query(RegradeRequest).filter(
            RegradeRequest.submission_id.in_(
                db.session.query(Submission.id).filter(
                    Submission.assignment_id.in_(assignment_ids)
                )
            )
        ).delete(synchronize_session=False)

        db.session.query(Submission).filter(
            Submission.assignment_id.in_(assignment_ids)
        ).delete(synchronize_session=False)

        db.session.query(Assignment).filter(
            Assignment.course_id == course_id
        ).delete(synchronize_session=False)

        db.session.commit()

        return jsonify("Assignments deleted successfully"), 200
    
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Failed to delete assignments")

@course.route("/create_enrollment", methods=["POST"])
@cross_origin()
def create_enrollment():
    """
    /create_enrollment enrolls a student in a course
    Requires from the frontend a JSON containing:
    @param student_id       the id of the student
    @param course_id        the id of the course
    """
    data = request.json
    required_fields = ["student_id", "course_id"]

    if not all(field in data for field in required_fields):
        raise BadRequestError("Missing required fields")

    if db.session.query(Enrollment).filter_by(student_id=data["student_id"], course_id=data["course_id"]).first():
        raise ConflictError("User is already enrolled in this course")

    role = data.get("role", "student")

    enrollment = Enrollment(
        student_id=data["student_id"],
        course_id=data["course_id"],
        role=role,
    )

    try:
        db.session.add(enrollment)
        db.session.commit()
        newEnrollment = EnrollmentSchema().dump(enrollment, many=False)
        return jsonify(newEnrollment), 201
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Failed to create enrollment")

@course.route("/update_role", methods=["POST"])
@cross_origin()
def update_role():
    data = request.json
    required_fields = ["student_id", "course_id", "new_role"]

    if not all(field in data for field in required_fields):
        raise BadRequestError("Missing required fields")

    # Update the role in the database
    enrollment = db.session.query(Enrollment).filter_by(student_id=data["student_id"], course_id=data["course_id"]).first()
    if not enrollment:
        raise NotFoundError("Enrollment not found")
    
    try:
        enrollment.role = data["new_role"]
        db.session.commit()
        newEnrollment = EnrollmentSchema().dump(enrollment, many=False)
        return jsonify(newEnrollment), 200
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Failed to update role")

# converted to a helper as a part of issue #41, to facilitate create_enrollment_csv()
def create_enrollment_bulk(data):
    """
    /create_enrollment_bulk mass enrolls students in a course
    Requires from the frontend a JSON containing:
    @param course_id        the id of the course
    @param student_ids      a list of student ids
    """
    course_id = data["course_id"]
    students = data["student_ids"]
    # default role to student if not present
    role = data.get("role", "student")

    if not course_id or not students:
        raise BadRequestError("Missing required fields")

    # remove duplicates in students
    students = list(set(students))

    failed_enrollments = []

    for student_id in students:
        try:
            enrollment = Enrollment(
                student_id=student_id,
                course_id=course_id,
                role=role
            )
            db.session.add(enrollment)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            failed_enrollments.append((student_id, "Already enrolled"))
        except Exception:
            db.session.rollback()
            failed_enrollments.append((student_id, "Enrollment failed"))
    
    return {
        "failed_enrollments": [{"id": sid, "reason": reason} for sid, reason in failed_enrollments]
    }

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@course.route("/create_enrollment_csv", methods=["POST"])
@cross_origin()
def create_enrollment_csv():
    if 'file' not in request.files:
        raise BadRequestError("Missing file part")
    
    file = request.files['file']

    if file.filename == '':
        raise BadRequestError("No selected file")

    if not allowed_file(file.filename):
        raise BadRequestError("Invalid file type")

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        file.save(file_path)
    except Exception:
        raise InternalProcessingError("Failed to save file")

    student_ids = []
    course_id = request.form.get("course_id")

    if not course_id:
        raise BadRequestError("Missing course_id")
    
    pre_failed = []

    try:
        with open(file_path, newline='') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            rows = list(csv_reader)
    except Exception:
        raise InternalProcessingError("Failed to process file")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    if not rows:
        raise BadRequestError("CSV file is empty")

    header = [col.strip().lower() for col in rows[0]]
    email_aliases = {"email", "email address"}
    matched = [col for col in header if col in email_aliases]
    if not matched:
        raise BadRequestError("CSV must contain an 'Email' or 'Email Address' column header")

    email_col = header.index(matched[0])
    role_col = header.index("role") if "role" in header else None

    id_to_email = {}

    for row in rows[1:]:
        if not row or len(row) <= email_col:
            continue
        email = row[email_col].strip()
        if not email:
            continue
        user = User.query.filter_by(email_address=email).first()
        if not user:
            pre_failed.append({"email": email, "reason": "User not found"})
            continue
        uid = str(user.id)
        id_to_email[uid] = email
        student_ids.append(uid)

    role = "student"
    if role_col and len(rows) > 1 and len(rows[1]) > role_col:
        role = rows[1][role_col].strip().lower() or "student"

    if not student_ids:
        return jsonify({"failed_enrollments": pre_failed}), 200

    response = create_enrollment_bulk({
        "course_id": course_id,
        "student_ids": student_ids,
        "role": role
    })

    response["failed_enrollments"] = [
        {"email": id_to_email.get(f["id"], f["id"]), "reason": f["reason"]}
        for f in response["failed_enrollments"]
    ] + pre_failed

    return jsonify(response), 200

@course.route("/get_user_enrollments", methods=["GET"])
@cross_origin()
def get_user_enrollments():
    """
    /get_user_enrollments gets all enrollments for a single user
    Requires from the frontend a JSON containing:
    @param user_id       the id of the user
    """
    user_id = request.args.get("user_id")
    if not user_id or user_id == "":
        raise BadRequestError("Missing user_id argument")
    
    enrollments = db.session.query(Enrollment).filter_by(student_id=user_id)
    course_ids = [course.course_id for course in enrollments]
    courses_query = db.session.query(Course).filter(Course.id.in_(course_ids))
    courses = CourseSchema().dump(courses_query, many=True)

    return jsonify(courses), 200

@course.route("/get_course_enrollment", methods=["GET"])
@cross_origin()
def get_course_enrollment():
    """
    Returns all users enrolled in a course,
    showing their course-specific role from the Enrollment table.
    """
    course_id = request.args.get("course_id")
    if not course_id:
        raise BadRequestError("Missing course_id argument")

    results = (
        db.session.query(
            User.id,
            User.name,
            User.email_address,
            Enrollment.role.label("role")
        )
        .join(Enrollment, Enrollment.student_id == User.id)
        .filter(Enrollment.course_id == course_id)
        .all()
    )

    data = [
        {
            "id": r.id,
            "name": r.name,
            "email_address": r.email_address,
            "role": r.role
        }
        for r in results
    ]
    return jsonify(data), 200


@course.route("/get_course_assignments", methods=["GET"])
@cross_origin()
def get_course_assignments():
    """
    /get_course_assignments gets all assignments for a course
    Requires from the frontend a JSON containing:
    @param course_id        the id of a course
    """
    course_id = request.args.get("course_id")
    if not course_id or course_id == "":
        raise BadRequestError("Missing course_id argument")
    
    assignments = db.session.query(Assignment).filter_by(course_id=course_id).all()
    assignments = AssignmentSchema().dump(assignments, many=True)

    return jsonify(assignments), 200


@course.route("/get_course_info", methods=["GET"])
@cross_origin()
def get_course_info():
    course_id = request.args.get("course_id")

    if not course_id or course_id == "":
        raise BadRequestError("Missing course_id argument")

    course_obj = db.session.query(Course).filter_by(id=course_id).first()

    if not course_obj:
        raise NotFoundError("Course not found")

    course_data = CourseSchema().dump(course_obj)

    course_data.update({
        "default_ai_provider": course_obj.default_ai_provider,
        "default_ai_model": course_obj.default_ai_model,
        "default_feedback_style": course_obj.default_feedback_style,
        "default_ai_temperature": course_obj.default_ai_temperature,

        "has_openai_api_key": bool(course_obj.openai_api_key),
        "has_gemini_api_key": bool(course_obj.gemini_api_key),
        "has_claude_api_key": bool(course_obj.claude_api_key),
        "has_ollama_api_key": bool(course_obj.ollama_base_url),
    })

    return jsonify([course_data]), 200

@course.route("/store_api_key", methods=["PUT"])
@cross_origin()

def store_api_key():
    """
    /store_api_key stores an encrypted OpenAI API key for a course.
    Requires:
    @param course_id: The UUID of the course.
    @param api_key: The plaintext OpenAI API key.
    """
    data = request.json
    required_fields = ["course_id", "api_key"]

    if not all(field in data and data[field] for field in required_fields):
        raise BadRequestError("Missing required fields")

    # Fetch the course
    course = db.session.query(Course).filter_by(id=data["course_id"]).first()
    if not course:
        raise NotFoundError("Course not found")

    # Encrypt API key before storing
    encrypted_api_key = encrypt_api_key(data["api_key"])

    try:
        course.openai_api_key = encrypted_api_key
        db.session.commit()
        return jsonify({"message": "API key stored securely"}), 200
    except Exception as e:
        db.session.rollback()
        raise InternalProcessingError("Failed to store API key")

@course.route("/update_ai_settings", methods=["PUT"])
@cross_origin()
def update_ai_settings():
    data = request.json

    course_id = data.get("course_id")
    provider = data.get("provider")
    model_name = data.get("model_name")
    api_key = data.get("api_key")
    feedback_style = data.get("feedback_style")
    temperature = data.get("temperature")

    if not course_id:
        raise BadRequestError("Missing course_id")

    course_obj = db.session.query(Course).filter_by(id=course_id).first()

    if not course_obj:
        raise NotFoundError("Course not found")

    if provider and provider not in SUPPORTED_AI_PROVIDERS:
        raise BadRequestError("Unsupported AI provider")

    if provider:
        course_obj.default_ai_provider = provider

    if model_name:
        course_obj.default_ai_model = model_name

    if feedback_style:
        course_obj.default_feedback_style = feedback_style

    if temperature is not None:
        try:
            temperature_value = float(temperature)
        except (TypeError, ValueError):
            raise BadRequestError("Invalid temperature")

        if temperature_value < 0 or temperature_value > 1:
            raise BadRequestError("Temperature must be between 0 and 1")

        course_obj.default_ai_temperature = temperature_value

    if api_key:
        if not provider:
            raise BadRequestError("Missing provider for API key")

        if provider == "ollama":
            course_obj.ollama_base_url = api_key.strip() if api_key else ""
        else:
            encrypted_api_key = encrypt_api_key(api_key)

            if provider == "openai":
                course_obj.openai_api_key = encrypted_api_key
            elif provider == "gemini":
                course_obj.gemini_api_key = encrypted_api_key
            elif provider == "claude":
                course_obj.claude_api_key = encrypted_api_key

    try:
        db.session.commit()
        return jsonify({"message": "AI settings updated successfully"}), 200
    except Exception:
        db.session.rollback()
        raise InternalProcessingError("Failed to update AI settings")


@course.route("/fetch_ai_models", methods=["POST"])
@cross_origin()
def fetch_ai_models():
    data = request.json

    course_id = data.get("course_id")
    provider = data.get("provider")
    api_key = data.get("api_key")

    if not provider:
        raise BadRequestError("Missing provider")

    try:
        if not api_key:
            if not course_id:
                raise BadRequestError("Missing course_id or api_key")

            course_obj = db.session.query(Course).filter_by(id=course_id).first()

            if not course_obj:
                raise NotFoundError("Course not found")

            if provider == "openai" and course_obj.openai_api_key:
                api_key = decrypt_api_key(course_obj.openai_api_key)
            elif provider == "gemini" and course_obj.gemini_api_key:
                api_key = decrypt_api_key(course_obj.gemini_api_key)
            elif provider == "claude" and course_obj.claude_api_key:
                api_key = decrypt_api_key(course_obj.claude_api_key)
            elif provider == "ollama" and course_obj.ollama_base_url:
                api_key = course_obj.ollama_base_url
            else:
                raise BadRequestError(f"No saved API key for {provider}")

        if provider == "ollama":
            base_url = (api_key or "http://host.docker.internal:11434").strip()
            try:
                response = requests.get(f"{base_url}/api/tags", timeout=10)
                if response.status_code >= 400:
                    current_app.logger.error(f"Ollama returned error: {response.text}")
                    return jsonify({"error": "Failed to retrieve models from Ollama"}), response.status_code
                
                models_data = response.json().get("models", [])
                model_ids = [m.get("name") for m in models_data if m.get("name")]
                return jsonify({"models": sorted(list(set(model_ids)))}), 200
            except Exception as e:
                current_app.logger.error(f"Failed to connect to Ollama at {base_url}: {str(e)}")
                return jsonify({"error": "Failed to connect to Ollama server"}), 500

        if provider == "openai":
            client = OpenAI(api_key=api_key)
            models_response = client.models.list()

            model_ids = [
                model.id
                for model in models_response.data
                if is_supported_openai_model(model.id)
            ]

            preferred_order = [
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-4.1-mini",
                "gpt-4.1",
            ]

            sorted_models = sorted(
                set(model_ids),
                key=lambda model: (
                    preferred_order.index(model)
                    if model in preferred_order
                    else len(preferred_order),
                    model
                )
            )

            return jsonify({"models": sorted_models}), 200

        if provider == "gemini":
            response = requests.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": api_key},
                timeout=30,
            )

            if response.status_code >= 400:
                return jsonify({"error": response.text}), response.status_code

            models_data = response.json().get("models", [])

            model_ids = []
            for model in models_data:
                model_name = model.get("name", "").replace("models/", "")
                supported_methods = model.get("supportedGenerationMethods", [])

                if (
                    "generateContent" in supported_methods
                    and is_supported_gemini_model(model_name)
                ):
                    model_ids.append(model_name)

            preferred_order = [
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-2.5-flash",
                "gemini-2.5-pro",
            ]

            sorted_models = sorted(
                set(model_ids),
                key=lambda model: (
                    preferred_order.index(model)
                    if model in preferred_order
                    else len(preferred_order),
                    model
                )
            )

            return jsonify({"models": sorted_models}), 200

        if provider == "claude":
            response = requests.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                timeout=30,
            )

            if response.status_code >= 400:
                return jsonify({"error": response.text}), response.status_code

            models_data = response.json().get("data", [])

            model_ids = [
                model.get("id")
                for model in models_data
                if model.get("id") and is_supported_claude_model(model.get("id"))
            ]

            preferred_order = [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-5-sonnet-latest",
                "claude-3-5-haiku-latest",
                "claude-3-opus-latest",
            ]

            sorted_models = sorted(
                set(model_ids),
                key=lambda model: (
                    preferred_order.index(model)
                    if model in preferred_order
                    else len(preferred_order),
                    model
                )
            )

            return jsonify({"models": sorted_models}), 200

        raise BadRequestError("Unsupported AI provider")

    except (BadRequestError, NotFoundError):
        raise
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@course.route("/test_ai_api_key", methods=["POST"])
@cross_origin()
def test_ai_api_key():
    data = request.json

    course_id = data.get("course_id")
    provider = data.get("provider")
    api_key = data.get("api_key")

    if not provider:
        raise BadRequestError("Missing provider")

    try:
        if not api_key:
            if not course_id:
                raise BadRequestError("Missing course_id or api_key")

            course_obj = db.session.query(Course).filter_by(id=course_id).first()

            if not course_obj:
                raise NotFoundError("Course not found")

            if provider == "openai" and course_obj.openai_api_key:
                api_key = decrypt_api_key(course_obj.openai_api_key)
            elif provider == "gemini" and course_obj.gemini_api_key:
                api_key = decrypt_api_key(course_obj.gemini_api_key)
            elif provider == "claude" and course_obj.claude_api_key:
                api_key = decrypt_api_key(course_obj.claude_api_key)
            elif provider == "ollama" and course_obj.ollama_base_url:
                api_key = course_obj.ollama_base_url
            else:
                raise BadRequestError(f"No saved API key for {provider}")

        if provider == "openai":
            client = OpenAI(api_key=api_key)
            client.models.list()

            return jsonify({
                "message": "OpenAI API key is valid",
                "provider": provider,
            }), 200

        if provider == "gemini":
            response = requests.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": api_key},
                timeout=30,
            )

            if response.status_code >= 400:
                return jsonify({
                    "error": f"Gemini API key test failed: {response.text}"
                }), response.status_code

            return jsonify({
                "message": "Gemini API key is valid",
                "provider": provider,
            }), 200

        if provider == "claude":
            response = requests.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                timeout=30,
            )

            if response.status_code >= 400:
                return jsonify({
                    "error": f"Claude API key test failed: {response.text}"
                }), response.status_code

            return jsonify({
                "message": "Claude API key is valid",
                "provider": provider,
            }), 200

        if provider == "ollama":
            base_url = (api_key or "http://host.docker.internal:11434").strip()
            try:
                response = requests.get(f"{base_url}/api/tags", timeout=10)
                if response.status_code >= 400:
                    current_app.logger.error(f"Ollama connection test failed: {response.text}")
                    return jsonify({
                        "error": "Ollama connection test failed"
                    }), response.status_code

                return jsonify({
                    "message": "Ollama connection is valid",
                    "provider": provider,
                }), 200
            except Exception as e:
                current_app.logger.error(f"Ollama connection error at {base_url}: {str(e)}")
                return jsonify({"error": "Ollama connection error"}), 500

        raise BadRequestError("Unsupported AI provider")

    except (BadRequestError, NotFoundError):
        raise
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@course.route("/test_ai_model", methods=["POST"])
@cross_origin()
def test_ai_model():
    data = request.json

    course_id = data.get("course_id")
    provider = data.get("provider")
    model = data.get("model")
    api_key = data.get("api_key")

    if not provider:
        raise BadRequestError("Missing provider")

    if not model:
        raise BadRequestError("Missing model")

    try:
        if not api_key:
            if not course_id:
                raise BadRequestError("Missing course_id or api_key")

            course_obj = db.session.query(Course).filter_by(id=course_id).first()

            if not course_obj:
                raise NotFoundError("Course not found")

            if provider == "openai" and course_obj.openai_api_key:
                api_key = decrypt_api_key(course_obj.openai_api_key)
            elif provider == "gemini" and course_obj.gemini_api_key:
                api_key = decrypt_api_key(course_obj.gemini_api_key)
            elif provider == "claude" and course_obj.claude_api_key:
                api_key = decrypt_api_key(course_obj.claude_api_key)
            elif provider == "ollama" and course_obj.ollama_base_url:
                api_key = course_obj.ollama_base_url
            else:
                raise BadRequestError(f"No saved API key for {provider}")

        test_prompt = (
            "Return only this JSON object: "
            "{\"insights\":[\"Model test passed.\"],\"annotations\":[]}"
        )

        def validate_feedback_response(raw_response, provider_name):
            parsed_feedback, _ = parse_feedback_json(raw_response, provider_name, [])

            if isinstance(parsed_feedback, dict) and parsed_feedback.get("error"):
                return None

            return parsed_feedback

        if provider == "openai":
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Return only valid JSON.",
                    },
                    {
                        "role": "user",
                        "content": test_prompt,
                    },
                ],
                max_tokens=80,
                temperature=0,
                response_format={"type": "json_object"},
                timeout=30,
            )

            raw_response = (response.choices[0].message.content or "").strip()
            parsed_feedback = validate_feedback_response(raw_response, "OpenAI")

            if parsed_feedback is None:
                return jsonify({
                    "error": "Selected OpenAI model did not return valid JSON feedback"
                }), 400

            return jsonify({
                "message": "OpenAI model is usable",
                "provider": provider,
                "model": model,
                "response": parsed_feedback,
            }), 200

        if provider == "gemini":
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": api_key},
                json={
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {
                                    "text": f"{CORRECTNESS_SYSTEM_PROMPT}\n\n{test_prompt}",
                                }
                            ],
                        }
                    ],
                    "generationConfig": get_gemini_generation_config(model, 0),
                },
                timeout=30,
            )

            if response.status_code >= 400:
                return jsonify({
                    "error": f"Selected Gemini model cannot be used: {response.text}"
                }), response.status_code

            data = response.json()
            candidate = data.get("candidates", [{}])[0]
            raw_response = "".join(
                part.get("text", "")
                for part in candidate.get("content", {}).get("parts", [])
                if not part.get("thought")
            )
            parsed_feedback = validate_feedback_response(raw_response, "Gemini")

            if parsed_feedback is None:
                return jsonify({
                    "error": "Selected Gemini model did not return valid JSON feedback"
                }), 400

            return jsonify({
                "message": "Gemini model is usable",
                "provider": provider,
                "model": model,
                "response": parsed_feedback,
            }), 200

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
                    "max_tokens": 80,
                    "system": "Return only valid JSON.",
                    "messages": [
                        {
                            "role": "user",
                            "content": test_prompt,
                        }
                    ],
                },
                timeout=30,
            )

            if response.status_code >= 400:
                return jsonify({
                    "error": f"Selected Claude model cannot be used: {response.text}"
                }), response.status_code

            data = response.json()
            content = data.get("content", [])
            raw_response = ""
            if content and content[0].get("type") == "text":
                raw_response = content[0].get("text", "")

            parsed_feedback = validate_feedback_response(raw_response, "Claude")

            if parsed_feedback is None:
                return jsonify({
                    "error": "Selected Claude model did not return valid JSON feedback"
                }), 400

            return jsonify({
                "message": "Claude model is usable",
                "provider": provider,
                "model": model,
                "response": parsed_feedback,
            }), 200

        if provider == "ollama":
            base_url = (api_key or "http://host.docker.internal:11434").strip()
            try:
                response = requests.post(
                    f"{base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": [
                            {"role": "user", "content": test_prompt}
                        ],
                        "options": {
                            "temperature": 0
                        },
                        "stream": False,
                        "format": "json"
                    },
                    timeout=15
                )
                if response.status_code >= 400:
                    current_app.logger.error(f"Selected Ollama model cannot be used: {response.text}")
                    return jsonify({
                        "error": "Selected Ollama model cannot be used"
                    }), response.status_code

                raw_response = response.json().get("message", {}).get("content", "").strip()
                parsed_feedback = validate_feedback_response(raw_response, "Ollama")

                if parsed_feedback is None:
                    current_app.logger.error(f"Selected Ollama model did not return valid JSON feedback. Raw response: {raw_response}")
                    return jsonify({
                        "error": "Selected Ollama model did not return valid JSON feedback"
                    }), 400

                return jsonify({
                    "message": "Ollama model is usable",
                    "provider": provider,
                    "model": model,
                    "response": parsed_feedback,
                }), 200
            except Exception as e:
                current_app.logger.error(f"Ollama connection error at {base_url}: {str(e)}")
                return jsonify({"error": "Ollama connection error"}), 500

        raise BadRequestError("Unsupported AI provider")

    except (BadRequestError, NotFoundError):
        raise
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@course.route("/get_courses_by_instructor", methods=["GET"])
@cross_origin()
def get_courses_by_instructor():
    """
    /get_courses_by_instructor gets all courses where the user is an instructor
    Requires from the frontend a query param:
    @param instructor_id    the id of the instructor
    """
    instructor_id = request.args.get("instructor_id")
    if not instructor_id or instructor_id == "":
        raise BadRequestError("Missing instructor_id argument")
    
    # Find all enrollments where this user is an instructor
    enrollments = db.session.query(Enrollment).filter_by(student_id=instructor_id, role="instructor").all()
    course_ids = [enrollment.course_id for enrollment in enrollments]
    if not course_ids:
        return jsonify([]), 200

    courses = db.session.query(Course).filter(Course.id.in_(course_ids)).all()
    return jsonify(CourseSchema(many=True).dump(courses)), 200
