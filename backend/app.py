from flask import Flask, flash, request, jsonify
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import docker_client
import uuid
from api import app, db
from api.models import Student

ALLOWED_EXTENSIONS = {'py','zip'}
UPLOAD_FOLDER = '/usr/app/files'
 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
 
@app.route('/')
def hello_world():
    print(db.session.query(Student))
    return 'Hello World'

def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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