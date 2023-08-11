"""Flask APP configuration."""
from os import environ, path
from dotenv import load_dotenv


# Specificy a `.env` file containing key/value config values
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, ".env"))


# General Config
# ENVIRONMENT = environ.get("ENVIRONMENT")
# FLASK_APP = environ.get("FLASK_APP")
# FLASK_DEBUG = environ.get("FLASK_DEBUG")

SECRET_KEY = environ.get("SECRET_KEY")
UPLOAD_FOLDER = "/usr/app/files"
SQLALCHEMY_DATABASE_URI = environ.get("DB_CONNECTION_STRING")