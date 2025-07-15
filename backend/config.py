import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DB_CONNECTION_STRING')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True