from flask import Flask, flash, request, jsonify
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import docker_client
import uuid
from api import app, db
from api.models import *
from api.schemas import *

ALLOWED_EXTENSIONS = {'py','zip'}
UPLOAD_FOLDER = '/usr/app/files'
 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
 
@app.route('/')
def hello_world():
    res = db.session.query(Student).first()
    print("results",res,"here")
    return 'Hello World'

def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create_student', methods=["POST"])
@cross_origin()
def create_student():
    user_id = str(uuid.uuid4())
    name = request.form['name']
    password = request.form['password']
    email_address = request.form['email']

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

    return jsonify(res)

@app.route('/student_login', methods=["POST"])
@cross_origin()
def student_login():
    email = request.form['email']
    password = request.form['password']

    res = db.session.query(Student).filter_by(email_address=email, password=password)
    res = StudentSchema().dump(res, many=True)

    return jsonify(res)

@app.route('/create_instructor', methods=["POST"])
@cross_origin()
def create_instructor():
    user_id = str(uuid.uuid4())
    name = request.form['name']
    password = request.form['password']
    email_address = request.form['email']

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

@app.route('/instructor_login', methods=["POST"])
@cross_origin()
def instructor_login():
    email = request.form['email']
    password = request.form['password']

    res = db.session.query(Instructor).filter_by(email_address=email, password=password)
    res = InstructorSchema().dump(res, many=True)

    return jsonify(res)

@app.route('/create_course', methods=["POST"])
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

@app.route('/create_assignment', methods=["POST"])
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

@app.route('/create_enrollment', methods=["POST"])
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
    
@app.route('/upload', methods=["GET", "POST"])
@cross_origin()
def upload_file():
    if "file" not in request.files:
        flash("No file part")
        return "no file"
    file = request.files["file"]
    assignment = request.form["assignment"].lower()

    if file.filename == "":
        flash("No selected file")
        return "no selected file"
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        new_uuid = str(uuid.uuid4())

        logs, results = docker_client.run_container(assignment, file, filename, new_uuid)

        return jsonify(logs=logs, results=results)

    if file and not allowed_file(file.filename):
        return "invalid extension"
 
if __name__ == '__main__':
    app.run()