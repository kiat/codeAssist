from .user import user as user_blueprint
from .course import course as course_blueprint
from .assignment import assignment as assignment_blueprint
from .ai_feedback import ai_feedback as ai_feedback_blueprint
from .regrade_request import regrade_request as regrade_request_blueprint
from .submission import submission as submission_blueprint
from .code_editor import code_editor as code_editor_blueprint

def register_routes(app):
    # Register all blueprints
    app.register_blueprint(user_blueprint)
    app.register_blueprint(course_blueprint)
    app.register_blueprint(assignment_blueprint)
    app.register_blueprint(ai_feedback_blueprint)
    app.register_blueprint(regrade_request_blueprint)
    app.register_blueprint(submission_blueprint)
    app.register_blueprint(code_editor_blueprint)
