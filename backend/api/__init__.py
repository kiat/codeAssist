from flask import Flask
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate  # Import Migrate
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = 'codeassist'
CORS(app)

load_dotenv()
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_CONNECTION_STRING")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = '/usr/app/files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ma = Marshmallow(app)
db = SQLAlchemy(app)

# Initialize Migrate with the Flask app and SQLAlchemy db instance
migrate = Migrate(app, db)

from api import models