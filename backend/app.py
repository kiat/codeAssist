from flask import Flask
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

def create_app():
    app = Flask(__name__)
    app.secret_key('codeassist')
    CORS(app)
    load_dotenv()
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_CONNECTION_STRING")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    ma = Marshmallow(app)
    db = SQLAlchemy(app)

    # attach blueprints here!


    return app

if __name__ == "__main__":
    create_app().run()