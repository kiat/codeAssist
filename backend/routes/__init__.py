from flask import Blueprint

from .user import user
from .course import course
from .assignment import assignment
from .regrade_request import regrade_request
from .submission import submission

def register_routes(app):
    # Register all blueprints
    app.register_blueprint(user)
    app.register_blueprint(course)
    app.register_blueprint(assignment)
    app.register_blueprint(regrade_request)
    app.register_blueprint(submission)

