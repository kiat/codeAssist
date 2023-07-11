from flask import Flask
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = 'codeassist'
CORS(app)

load_dotenv()
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_CONNECTION_STRING")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# change the upload folder as necessary - this application can only see from the cwd if run locally
UPLOAD_FOLDER = '/usr/app/files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ma = Marshmallow(app)
db = SQLAlchemy(app)

from api import routes, models