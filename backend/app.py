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

@app.route('/create_user', methods=["POST"])
@cross_origin()
def create_user():
    user_id = str(uuid.uuid4())
    name = request.json['name']
    password = request.json['password']
    email_address=request.json['email']

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

@app.route('/create_course', methods=["POST"])
@cross_origin()
def create_course():
    course_id = str(uuid.uuid4())
    name = request.json['name']

    course_data = {
        "id": course_id,
        "name": name,
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