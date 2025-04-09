import uuid
import os
import csv
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
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

course = Blueprint("course", __name__)

ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_FOLDER = 'uploads'

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
        except Exception:
            failed_enrollments.append(student_id)
    
    return {
        "failed_enrollments" : failed_enrollments
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
    
    try:
        with open(file_path, newline='')  as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            for row in csv_reader:
                student_ids.append(row[0])
    except Exception as e:
        raise InternalProcessingError("Failed to process file")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    response = create_enrollment_bulk({
        "course_id": course_id,
        "student_ids": student_ids
        })

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
    /get_course_enrollment gets all students enrolled in a course
    Requires from the frontend a JSON containing:
    @param course_id        the id of a course
    """
    course_id = request.args.get("course_id")
    if not course_id or course_id == "":
        raise BadRequestError("Missing course_id argument")

    students = db.session.query(Enrollment.student_id).filter_by(course_id=course_id)
    students = EnrollmentSchema().dump(students, many=True)

    list_of_students = [x["student_id"] for x in students]

    students = db.session.query(
        User.name, User.email_address, User.id, User.role
    ).filter(User.id.in_(list_of_students))
    students = UserSchema().dump(students, many=True)

    return jsonify(students)


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

    course = db.session.query(Course).filter_by(id=course_id)
    course = CourseSchema().dump(course, many=True)

    return jsonify(course), 200
