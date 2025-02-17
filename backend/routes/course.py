import uuid
import os
import csv
from flask import Blueprint, request, jsonify, make_response
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
    Enrollment,
)
from api.schemas import AssignmentSchema, CourseSchema, EnrollmentSchema, UserSchema

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
    course_id = str(uuid.uuid4())
    name = request.json["name"]
    instructor_id = request.json["instructor_id"]
    semester = request.json["semester"]
    year = request.json["year"]
    entryCode = request.json["entryCode"]

    if not name or not instructor_id or not semester or not year or not entryCode:
        return jsonify({"message": "Missing required fields"}), 400

    existing_course = db.session.query(Course).filter_by(entryCode=entryCode).first()
    if existing_course:
        return jsonify({"message": "Course with the provided entry code already exists"}), 409

    course_data = {
        "id": course_id,
        "name": name,
        "instructor_id": instructor_id,
        "semester": semester,
        "year": year,
        "entryCode": entryCode,
    }

    enrollment_data = {
        "student_id": instructor_id,
        "course_id": course_id,
        "role": "instructor",
    }

    try:
        db.session.add(Course(**course_data))
        db.session.add(Enrollment(**enrollment_data))
        db.session.commit()
        newCourse = db.session.query(Course).filter_by(id=course_id)
        newCourse = CourseSchema().dump(newCourse, many=True)[0]
        return jsonify(newCourse), 201
    except Exception as e:
        return jsonify({"message": "An unexpected error occurred."}), 500


@course.route("/enroll_course", methods=["POST", "GET"])
@cross_origin()
def enroll_course():
    """
    /enroll_course enrolls a student in a course using entryCode
    Requires from the frontend a JSON containing:
    @param entryCode        entryCode of the course
    @param user_id       id of the student
    """
    student_id = request.json["user_id"]
    entryCode = request.json["entryCode"]

    enrolledCourse = db.session.query(Course).filter_by(entryCode=entryCode)
    enrolled_list = [enroll.id for enroll in enrolledCourse]

    # Check if the course exists
    if not enrolled_list:
        return jsonify({"message": "Course with the provided entry code does not exist"}), 404

    enrollment_data = {
        "student_id": student_id,
        "course_id": enrolled_list[0],
        "role": "student",
    }
    db.session.add(Enrollment(**enrollment_data))
    db.session.commit()

    enrolledCourse = CourseSchema().dump(enrolledCourse, many=True)[0]

    return jsonify(enrolledCourse)


@course.route("/update_course", methods=["POST"])
@cross_origin()
def update_course():
    """
    /update_course updates a course in the database
    Requires from the frontend a JSON containing
    @param id               id of the course in database
    """
    course_id = request.json["course_id"]
    data = request.json
    del data["course_id"]

    name, val = list(data.keys()), list(data.values())
    updated_course_info = {getattr(Course, name): val for name, val in zip(name, val)}

    course = (
        db.session.query(Course).filter_by(id=course_id).update(updated_course_info)
    )
    db.session.commit()

    return jsonify({"message": "Success"}), 200


@course.route("/delete_course", methods=["DELETE"])
@cross_origin()
def delete_course():
    course_id = request.args.get("course_id")
    # Check if there are any assignments for this course
    related_assignments = (
        db.session.query(Assignment).filter_by(course_id=course_id).all()
    )
    if related_assignments:
        print("410")
        return jsonify("Assignments must be deleted"), 410

    enrollments = db.session.query(Enrollment).filter_by(course_id=course_id).all()
    if enrollments:
        for enrollment in enrollments:
            db.session.delete(enrollment)
        db.session.commit()

    # actually delete course
    course_to_delete = db.session.query(Course).get(course_id)
    if course_to_delete:
        db.session.delete(course_to_delete)
        db.session.commit()
        return jsonify("Course deleted successfully"), 200
    else:
        return jsonify("Course not found"), 404


@course.route("/delete_all_assignments", methods=["DELETE"])
@cross_origin()
def delete_all_assignments():
    course_id = request.args.get("course_id")

    # Check if there are any assignments for this course
    related_assignments = (
        db.session.query(Assignment).filter_by(course_id=course_id).all()
    )
    if related_assignments:
        for assignment in related_assignments:
            related_submissions = (
                db.session.query(Submission)
                .filter_by(assignment_id=assignment.id)
                .all()
            )
            if related_submissions:
                for submission in related_submissions:
                    related_requests = db.session.query(RegradeRequest).filter_by(
                        submission_id=submission.id
                    )
                    if related_requests:
                        for req in related_requests:
                            db.session.delete(req)
                    db.session.delete(submission)
                db.session.commit()
            db.session.delete(assignment)
        db.session.commit()

    related_assignments = (
        db.session.query(Assignment).filter_by(course_id=course_id).all()
    )
    if not related_assignments:
        return jsonify("Assignments deleted successfully"), 200
    else:
        return jsonify("Assignments not deleted"), 404


@course.route("/create_enrollment", methods=["POST"])
@cross_origin()
def create_enrollment():
    """
    /create_enrollment enrolls a student in a course
    Requires from the frontend a JSON containing:
    @param student_id       the id of the student
    @param course_id        the id of the course
    """
    student_id = request.json["student_id"]
    course_id = request.json["course_id"]
    role = request.json["role"]

    if not student_id or not course_id or not role:
        return jsonify({"message": "Missing required fields"}), 400

    enrollment_data = {
        "student_id": student_id,
        "course_id": course_id,
        "role": role,
    }

    existing_enrollment = db.session.query(Enrollment).filter_by(student_id=student_id, course_id=course_id).first()
    if existing_enrollment:
        return jsonify({"message": "Enrollment already exists"}), 409

    try:
        db.session.add(Enrollment(**enrollment_data))
        db.session.commit()
        newEnrollment = db.session.query(Enrollment).filter_by(
            student_id=student_id, course_id=course_id
        )
        newEnrollment = EnrollmentSchema().dump(newEnrollment, many=True)[0]
        return jsonify(newEnrollment), 201
    except Exception as e:
        return jsonify({"message": "An unexpected error occurred"}), 500

@course.route("/update_role", methods=["POST"])
@cross_origin()
def update_role():
    data = request.get_json()
    student_id = data.get("student_id")
    course_id = data.get("course_id")
    new_role = data.get("new_role")

    if not student_id or not course_id or not new_role:
        return jsonify({"error": "Missing required fields"}), 400

    # Update the role in the database
    enrollment = (
        db.session.query(Enrollment)
        .filter_by(student_id=student_id, course_id=course_id)
        .first()
    )
    if enrollment:
        enrollment.role = new_role
        db.session.commit()
        return jsonify({"message": "Role updated successfully"}), 200
    else:
        return jsonify({"error": "Enrollment not found"}), 404

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
        return jsonify({"error": "Missing required fields"}), 400

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
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    student_ids = []
    course_id = request.form.get("course_id")
    try:
        with open(file_path, newline='')  as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            for row in csv_reader:
                student_ids.append(row[0])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    response = create_enrollment_bulk({
        "course_id": course_id,
        "student_ids": student_ids
        })

    os.remove(file_path)

    res = make_response(jsonify(response), 200)
    return res

@course.route("/get_student_enrollments", methods=["GET"])
@cross_origin()
def get_student_enrollments():
    """
    /get_student_enrollments gets all enrollments for a single student
    Requires from the frontend a JSON containing:
    @param student_id       the id of the student
    """
    student_id = request.args.get("student_id")

    enrollments = db.session.query(Enrollment).filter_by(student_id=student_id)
    # enrollments = EnrollmentSchema().dump(enrollments, many=True)
    enrolled_list = [student_course.course_id for student_course in enrollments]
    student_courses = db.session.query(Course).filter(Course.id.in_(enrolled_list))
    student_courses = CourseSchema().dump(student_courses, many=True)
    # return jsonify(enrollments)
    return jsonify(student_courses)


@course.route("/get_course_enrollment", methods=["GET"])
@cross_origin()
def get_course_enrollment():
    """
    /get_course_enrollment gets all students enrolled in a course
    Requires from the frontend a JSON containing:
    @param course_id        the id of a course
    """
    course_id = request.args.get("course_id")

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

    assignments = db.session.query(Assignment).filter_by(course_id=course_id)
    assignments = AssignmentSchema().dump(assignments, many=True)

    return jsonify(assignments)


@course.route("/get_instructor_courses", methods=["GET"])
@cross_origin()
def get_instructor_courses():
    """
    /get_instructor_courses gets all the courses created by an instructor
    Requires from the frontend a JSON containing:
    @param instructor_id    the id of an instructor
    """
    instructor_id = request.args.get("instructor_id")

    course = db.session.query(Enrollment.course_id).filter_by(student_id=instructor_id)
    course = EnrollmentSchema().dump(course, many=True)

    list_of_courses = [x["course_id"] for x in course]

    courses = db.session.query(Course).filter(Course.id.in_(list_of_courses))
    courses = CourseSchema().dump(courses, many=True)

    return jsonify(courses)


@course.route("/get_course_info", methods=["GET"])
@cross_origin()
def get_course_info():
    course_id = request.args.get("course_id")
    course = db.session.query(Course).filter_by(id=course_id)
    course = CourseSchema().dump(course, many=True)

    return jsonify(course)


@course.route("/get_student_enrollment", methods=["GET"])
@cross_origin()
def get_student_enrollment():
    """
    /get_course_enrollment gets all students enrolled in a course
    Requires from the frontend a JSON containing:
    @param course_id        the id of a course
    """
    course_id = request.args.get("course_id")

    students = db.session.query(Enrollment.student_id).filter_by(
        course_id=course_id, role="student"
    )
    students = EnrollmentSchema().dump(students, many=True)

    list_of_students = [x["student_id"] for x in students]

    students = db.session.query(
        User.name, User.email_address, User.id, User.role
    ).filter(User.id.in_(list_of_students))
    students = UserSchema().dump(students, many=True)

    return jsonify(students)
