from . import assignment as assignment_routes
from . import code_editor as code_editor_routes
from . import course as course_routes
from . import regrade_request as regrade_request_routes
from . import submission as submission_routes
from . import user as user_routes

def register_routes(app):
    # Register all blueprints
    app.register_blueprint(user_routes.user)
    app.register_blueprint(course_routes.course)
    app.register_blueprint(assignment_routes.assignment)
    app.register_blueprint(regrade_request_routes.regrade_request)
    app.register_blueprint(submission_routes.submission)
    app.register_blueprint(code_editor_routes.code_editor)
