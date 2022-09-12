import os
from flask import Flask, flash, request, redirect, url_for
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import webbrowser
import docker_client
import uuid

ALLOWED_EXTENSIONS = {'py','zip'}
UPLOAD_FOLDER = '/Users/rickywoodruff/Desktop/UT Austin/Fall 2022 (Senior)/CS370/codeAssist/CodeAssist/backend/files'
 
app = Flask(__name__)
app.secret_key = 'codeassist'
cors = CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
 
@app.route('/')
def hello_world():
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

    if file.filename == "":
        flash("No selected file")
        return "no selected file"
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        new_uuid = uuid.uuid4()
        res = docker_client.run_container("test", file, filename, str(new_uuid))
        print(res)
        return res
    if file and not allowed_file(file.filename):
        return "invalid extension"
 
if __name__ == '__main__':
    app.run()