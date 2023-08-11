from flask import Flask, url_for
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy

def create_app(config_filename: str):
    app = Flask(__name__)
    app.config.from_pyfile(config_filename)
    CORS(app)

    return app

print("Starting Flask")
app = create_app("config.py")
db = SQLAlchemy(app)

@app.route('/', methods=["GET"])
@cross_origin()
def hello_world():
    '''
    This is the default response with no methods and extensions - '/'
    If you host the backend locally at localhost:5000 it should display "Hello World"
    '''
    return 'Hello World'

@app.route("/favicon.ico")
def favicon():
    '''
    This is to get rid of that annoying 404 error popping up in console for a favicon.
    '''
    return url_for('static', filename='data:,')

