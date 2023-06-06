from flask import Flask, flash, request, jsonify
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import docker_client
from functools import reduce
import json
import sys
import uuid
from api import app, db
from api.models import *
from api.schemas import *

ALLOWED_EXTENSIONS = {'py','zip'}
UPLOAD_FOLDER = '/usr/app/files'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=["GET", "POST"])
@cross_origin()
def hello_world():
    return 'Hello World'

def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create_student', methods=["GET", "POST"])
@cross_origin()
def create_student():
    if request.method != "POST":
        return "all good"
    user_id = str(uuid.uuid4())
    name = request.json['name']
    password = request.json['password']
    email_address = request.json['email']

    user_data = {
        "id": user_id,
        "name": name,
        "email_address": email_address,
        "password": password,
    }

    db.session.add(Student(**user_data))
    db.session.commit()

    res = db.session.query(Student).filter_by(id=user_id)
    res = StudentSchema().dump(res, many=True)[0]
    response = jsonify(res)
    return response

@app.route('/student_login', methods=["POST", "GET"])
@cross_origin()
def student_login():
    email = request.json['email']
    password = request.json['password']

    res = db.session.query(Student).filter_by(email_address=email, password=password)
    res = StudentSchema().dump(res, many=True)

    if len(res) == 0:
        return "No user found", 404

    return jsonify(res[0])

@app.route('/create_instructor', methods=["POST", "GET"])
@cross_origin()
def create_instructor():
    user_id = str(uuid.uuid4())
    name = request.json['name']
    password = request.json['password']
    email_address = request.json['email']

    user_data = {
        "id": user_id,
        "name": name,
        "email_address": email_address,
        "password": password,
    }

    db.session.add(Instructor(**user_data))
    db.session.commit()

    res = db.session.query(Instructor).filter_by(id=user_id)
    res = InstructorSchema().dump(res, many=True)[0]

    return jsonify(res)

@app.route('/instructor_login', methods=["POST", "GET"])
@cross_origin()
def instructor_login():
    email = request.json['email']
    password = request.json['password']

    res = db.session.query(Instructor).filter_by(email_address=email, password=password)
    res = InstructorSchema().dump(res, many=True)[0]

    return jsonify(res)

@app.route('/create_course', methods=["POST", "GET"])
@cross_origin()
def create_course():
    course_id = str(uuid.uuid4())
    name = request.json['name']
    instructor_id = request.json['instructor_id']

    course_data = {
        "id": course_id,
        "name": name,
        "instructor_id": instructor_id,
    }

    db.session.add(Course(**course_data))
    db.session.commit()

    newCourse = db.session.query(Course).filter_by(id=course_id)
    newCourse = CourseSchema().dump(newCourse, many=True)[0]

    return jsonify(newCourse)

@app.route('/update_assignment', methods=["POST", "GET"])
@cross_origin()
def update_course():
    assignment_id = request.json["assignment_id"]

    data = request.json
    del data["assignment_id"]

    assignment = db.session.query(Assignment).filter_by(id=assignment_id).update(data)
    db.session.commit()

    return jsonify({"message": "Success"}), 200

@app.route('/get_assignment', methods=["GET"])
@cross_origin()
def get_assignment():
    assignment_id = request.args.get("assignment_id")

    assignment = db.session.query(Assignment).filter_by(id=assignment_id)
    assignment = AssignmentSchema().dump(assignment, many=True)[0]

    return jsonify(assignment)


@app.route('/create_assignment', methods=["POST", "GET"])
@cross_origin()
def create_assignment():
    assignment_id = str(uuid.uuid4())
    name = request.json['name']
    course_id = request.json['course_id']

    assignment_data = {
        "id": assignment_id,
        "name": name,
        "course_id": course_id,
    }

    db.session.add(Assignment(**assignment_data))
    db.session.commit()

    newAssignment = db.session.query(Assignment).filter_by(id=assignment_id)
    newAssignment = AssignmentSchema().dump(newAssignment, many=True)[0]

    return jsonify(newAssignment)

@app.route('/create_enrollment', methods=["POST", "GET"])
@cross_origin()
def create_new_assignment():
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

@app.route('/create_enrollment_bulk', methods=["POST", "GET"])
@cross_origin()
def create_bulk_enrollments():
    course_id = request.json["course_id"]
    students = request.json["student_ids"]

    students_to_add = [Enrollment(**{
        "student_id": id,
        "course_id": course_id,
    }) for id in students]

    db.session.add_all(students_to_add)
    db.session.commit()

    return jsonify({"message":"Success"}), 200

@app.route('/get_student_enrollments', methods=["GET"])
@cross_origin()
def get_student_enrollments():
    student_id = request.args.get("student_id")

    enrollments = db.session.query(Enrollment).filter_by(student_id=student_id)
    enrollments = EnrollmentSchema().dump(enrollments, many=True)

    return jsonify(enrollments)

@app.route('/get_course_assignments', methods=["GET"])
@cross_origin()
def get_course_assignments():
    course_id = request.args.get("course_id")

    assignments = db.session.query(Assignment).filter_by(course_id=course_id)
    assignments = AssignmentSchema().dump(assignments, many=True)
    
    return jsonify(assignments)

@app.route('/get_course_enrollment', methods=["GET"])
@cross_origin()
def get_course_enrollment():
    course_id = request.args.get("course_id")

    students = db.session.query(Enrollment.student_id).filter_by(course_id=course_id)
    students = EnrollmentSchema().dump(students, many=True)

    list_of_students = [x["student_id"] for x in students]

    students = db.session.query(Student.name, Student.email_address).filter(Student.id.in_(list_of_students))
    students = StudentSchema().dump(students, many=True)

    return jsonify(students)
    

@app.route('/get_instructor_courses', methods=["GET"])
@cross_origin()
def get_instructor_courses():
    instructor_id = request.args.get("instructor_id")

    courses = db.session.query(Course).filter_by(instructor_id=instructor_id)
    courses = CourseSchema().dump(courses, many=True)

    return jsonify(courses)

@app.route('/get_submissions', methods=["GET"])
@cross_origin()
def get_submission():
    student_id = request.args.get("student_id")
    assignment_id = request.args.get("assignment_id")

    submissions = db.session.query(Submission).filter_by(student_id=student_id, assignment_id=assignment_id)
    submissions = SubmissionSchema().dump(submissions, many=True)

    return jsonify(submissions)
    
@app.route('/upload_submission', methods=["POST", "GET"])
@cross_origin()
def upload_file():
    if "file" not in request.files:
        flash("No file part")
        return "no file\n"
    file = request.files["file"]
    assignment = request.form["assignment"].lower()
    student_id = request.form["student_id"]
    assignment_id = request.form["assignment_id"]

    if file.filename == "":
        flash("No selected file")
        return "no selected file"
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        new_uuid = str(uuid.uuid4())

        submission_data = {
            "id": new_uuid,
            "student_id": student_id,
            "assignment_id": assignment_id,
            "student_code_file": file.read(),
            "completed": False
        }

        file.seek(0)

        db.session.add(Submission(**submission_data))
        db.session.commit()

        logs, results = docker_client.run_container(assignment, file, filename, new_uuid)

        submission_data["results"] = results.encode('utf8')
        submission_data["completed"] = True

        print(results, file=sys.stderr)
        tests = json.loads(results)["tests"]
        print(tests, file=sys.stderr)
        score = reduce(lambda x,y: x+y, list(map(lambda x: x["score"], tests)))
        print(score, file=sys.stderr)

        submission_data["score"] = score
        
        db.session.query(Submission).filter_by(id=new_uuid).update(submission_data)
        db.session.commit()

        new_submission = db.session.query(Submission).filter_by(id=new_uuid)
        new_submission = SubmissionSchema().dump(new_submission, many=True)[0]

        return jsonify(new_submission)

    if file and not allowed_file(file.filename):
        return "invalid extension"

@app.route('/upload_assignment_autograder', methods=["POST", "GET"])
@cross_origin()
def upload_assignment_autograder():
    if "file" not in request.files:
        flash("No file part")
        return "no file\n"
    file = request.files["file"]
    assignment_id = request.form["assignment_id"]

    if file.filename == "":
        flash("No selected file")
        return "no selected file"
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        docker_client.saveFile(file, filename, docker_client.assignment_dir, False)

        assignment_data = {
            'autograder_file': file.read(),
        }

        file.seek(0)

        assignment = db.session.query(Assignment).filter_by(id=assignment_id).update(assignment_data)
        db.session.commit()

        assignment = AssignmentSchema().dump(assignment, many=True)[0]

        return jsonify(assignment)
    else:
        return "something went wrong", 400

 
if __name__ == '__main__':
    app.run()
