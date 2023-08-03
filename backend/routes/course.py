import uuid
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from api import db
from api.models import Assignment, Course, Enrollment, Student
from api.schemas import AssignmentSchema, CourseSchema, EnrollmentSchema, StudentSchema

course = Blueprint('course', __name__)

@course.route('/create_course', methods=["POST", "GET"])
@cross_origin()
def create_course():
    '''
    /create_course creates a course in the database
    Requires from the frontend a JSON containing:
    @param name             name of the course
    @param instructor_id    TODO: What does this map to? @
    @param semester         semester of the course
    @param year             year of the course
    @param entryCode        entryCode of the course
    '''
    course_id = str(uuid.uuid4())
    name = request.json['name']
    instructor_id = request.json['instructor_id']
    semester = request.json['semester']
    year = request.json['year']
    entryCode = request.json["entryCode"]

    course_data = {
        "id": course_id,
        "name": name,
        "instructor_id": instructor_id,
        "semester": semester,
        "year": year,
        "entryCode": entryCode
    }

    db.session.add(Course(**course_data))
    db.session.commit()

    newCourse = db.session.query(Course).filter_by(id=course_id)
    newCourse = CourseSchema().dump(newCourse, many=True)[0]

    return jsonify(newCourse)

@course.route('/enroll_course', methods=["POST", "GET"])
@cross_origin()
def enroll_course():
    '''
    /enroll_course enrolls a student in a course using entryCode
    Requires from the frontend a JSON containing:
    @param entryCode        entryCode of the course
    @param student_id       id of the student
    '''
    student_id = request.json['student_id']
    entryCode = request.json['entryCode']
    enrolledCourse = db.session.query(Course).filter_by(entryCode=entryCode)
    enrolled_list = [enroll.id for enroll in enrolledCourse]

    enrollment_data = {
        "student_id": student_id,
        "course_id": enrolled_list[0],
    }
    db.session.add(Enrollment(**enrollment_data))
    db.session.commit()

    enrolledCourse = CourseSchema().dump(enrolledCourse, many=True)[0]

    return jsonify(enrolledCourse)

@course.route('/update_course', methods = ["POST"])
@cross_origin()
def update_course():
    '''
    /update_course updates a course in the database
    Requires from the frontend a JSON containing
    @param id               id of the course in database
    '''
    course_id = request.json["course_id"]
    data = request.json
    del data["course_id"]

    name, val = list(data.keys()), list(data.values())
    updated_course_info = {getattr(Course, name): val for name, val in zip(name, val)}

    course = db.session.query(Course).filter_by(id=course_id).update(updated_course_info)
    db.session.commit()

    return jsonify({"message": "Success"}), 200

@course.route('/delete_course', methods=["DELETE", "OPTIONS"])
@cross_origin()
def delete_course():
    '''
    /delete_course deletes a course from the database
    Requires from the frontend a JSON containing:
    @param course_id        the id of the course
    '''
    print(request)
    if request.method == "OPTIONS":
        return "", 200
    if request.method == "DELETE":
        course_id = request.args.get("course_id")
        course_to_delete = db.session.get(Course, course_id)
        try:
            db.session.delete(course_to_delete)
            db.session.commit()
        except:
            return "Error removing course"
        
@course.route('/create_enrollment', methods=["POST", "GET"])
@cross_origin()
def create_enrollment():
    
    '''
    /create_enrollment enrolls a student in a course
    Requires from the frontend a JSON containing:
    @param student_id       the id of the student
    @param course_id        the id of the course
    '''
    student_id = request.json["student_id"]
    course_id = request.json["course_id"]

    enrollment_data = {
        "student_id": student_id,
        "course_id": course_id,
    }

    db.session.add(Enrollment(**enrollment_data))
    db.session.commit()

    newEnrollment = db.session.query(Enrollment).filter_by(student_id=student_id, course_id=course_id)
    newEnrollment = EnrollmentSchema().dump(newEnrollment, many=True)[0]

    return jsonify(newEnrollment)

@course.route('/create_enrollment_bulk', methods=["POST", "GET"])
@cross_origin()
def create_enrollment_bulk():
    
    '''
    /create_enrollment_bulk mass enrolls students in a course
    Requires from the frontend a JSON containing:
    @param course_id        the id of the course
    @parma student_ids      a list of student ids
    '''
    course_id = request.json["course_id"]
    students = request.json["student_ids"]

    students_to_add = [Enrollment(**{
        "student_id": id,
        "course_id": course_id,
    }) for id in students]

    db.session.add_all(students_to_add)
    db.session.commit()

    return jsonify({"message":"Success"}), 200

@course.route('/get_student_enrollments', methods=["GET"])
@cross_origin()
def get_student_enrollments():
    '''
    /get_student_enrollments gets all enrollments for a single student
    Requires from the frontend a JSON containing:
    @param student_id       the id of the student
    '''
    student_id = request.args.get("student_id")

    enrollments = db.session.query(Enrollment).filter_by(student_id=student_id)
    #enrollments = EnrollmentSchema().dump(enrollments, many=True)
    enrolled_list = [student_course.course_id for student_course in enrollments]
    student_courses = db.session.query(Course).filter(Course.id.in_(enrolled_list))
    student_courses = CourseSchema().dump(student_courses, many=True)
    #return jsonify(enrollments)
    return jsonify(student_courses)

@course.route('/get_course_enrollment', methods=["GET"])
@cross_origin()
def get_course_enrollment():
    '''
    /get_course_enrollment gets all students enrolled in a course
    Requires from the frontend a JSON containing:
    @param course_id        the id of a course
    '''
    course_id = request.args.get("course_id")

    students = db.session.query(Enrollment.student_id).filter_by(course_id=course_id)
    students = EnrollmentSchema().dump(students, many=True)

    list_of_students = [x["student_id"] for x in students]

    students = db.session.query(Student.name, Student.email_address, Student.id).filter(Student.id.in_(list_of_students))
    students = StudentSchema().dump(students, many=True)

    return jsonify(students)

@course.route('/get_course_assignments', methods=["GET"])
@cross_origin()
def get_course_assignments():
    '''
    /get_course_assignments gets all assignments for a course
    Requires from the frontend a JSON containing:
    @param course_id        the id of a course
    '''
    course_id = request.args.get("course_id")

    assignments = db.session.query(Assignment).filter_by(course_id=course_id)
    assignments = AssignmentSchema().dump(assignments, many=True)
    
    return jsonify(assignments)

@course.route('/get_instructor_courses', methods=["GET"])
@cross_origin()
def get_instructor_courses():
    '''
    /get_instructor_courses gets all the courses created by an instructor
    Requires from the frontend a JSON containing:
    @param instructor_id    the id of an instructor
    '''
    instructor_id = request.args.get("instructor_id")

    courses = db.session.query(Course).filter_by(instructor_id=instructor_id)
    courses = CourseSchema().dump(courses, many=True)
   
    return jsonify(courses)

@course.route('/get_course_info', methods=["GET"])
@cross_origin()
def get_course_info():
    course_id = request.args.get("course_id")
    course = db.session.query(Course).filter_by(id=course_id)
    course = CourseSchema().dump(course, many=True)
    
    return jsonify(course)