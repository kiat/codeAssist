from autograder_models import *
from datetime import datetime
# import docker_client
from flask import Flask, url_for, request, jsonify, flash
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from functools import reduce
import json
import sys
from time import time 
import uuid
from werkzeug.utils import secure_filename

def create_app(config_filename: str):
    app = Flask(__name__)
    app.config.from_pyfile(config_filename)
    CORS(app)

    return app

print("Starting Flask")
app = create_app("config.py")
db = SQLAlchemy(app)
ma = Marshmallow(app)

ALLOWED_EXTENSIONS = {'py','zip'}

def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=["GET"])
@cross_origin()
def hello_world():
    '''
    This is the default response with no methods and extensions - '/'
    If you host the backend locally at localhost:5000 it should display "Hello World"
    '''
    return 'Hello World'

@app.route('/upload', methods=["POST"])
@cross_origin()
def upload():
    '''
    Testing upload CORS - no execution
    '''
    # currently only accepts a single file
    file = request.files["file"]
    new_uuid = str(uuid.uuid4())
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    submission_data = {
        "id": new_uuid,
        "student_code_file": file.read(),
        "results": None,
        "score": 12.34,
        "execution_time": 56.78,
        "executed_at": timestamp
    }
    db.session.add(Submission(**submission_data))
    db.session.commit()
    
    new_submission = db.session.query(Submission).filter_by(id=new_uuid)
    new_submission = SubmissionSchema().dump(new_submission, many=True)[0]
    return jsonify(new_submission)

@app.route('/upload_submission', methods=["POST"])
@cross_origin()
def upload_submission():
    '''
    Testing upload CORS - no execution
    '''
    # currently only accepts a single file
    file = request.files["file"]
    new_uuid = str(uuid.uuid4())
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    submission_data = {
        "id": new_uuid,
        "student_code_file": file.read(),
        "results": None,
        "score": 12.34,
        "execution_time": 56.78,
        "executed_at": timestamp
    }
    db.session.add(Submission(**submission_data))
    db.session.commit()
    
    new_submission = db.session.query(Submission).filter_by(id=new_uuid)
    new_submission = SubmissionSchema().dump(new_submission, many=True)[0]
    return jsonify(new_submission)

@app.route('/message', methods=["POST"])
@cross_origin()
def post_message():
    '''
    Testing POST for axios errors
    '''
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    message = request.json['message']

    message_data = {
        "timestamp": timestamp,
        "message": message,
    }
    db.session.add(Message(**message_data))
    db.session.commit()
    return jsonify({"message": "Success"}), 200

@app.route('/getlatestmessage', methods=["GET"])
@cross_origin()
def get_latest_message():
    '''
    Testing GET for axios errors
    '''
    latest_message = db.session.query(Message).order_by(Message.timestamp.desc()).first()
    print(jsonify(latest_message))
    # SubmissionSchema().dump(new_submission, many=True)[0]
    return jsonify(latest_message), 200

@app.route("/favicon.ico")
def favicon():
    '''
    This is to get rid of that annoying 404 error popping up in console for a favicon.
    '''
    return url_for('static', filename='data:,')