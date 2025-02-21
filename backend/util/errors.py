from flask import jsonify

class BadRequestError(Exception):
    status_code = 400
    def __init__(self, message="Bad request"):
        super().__init__(message)

class InternalProcessingError(Exception):
    status_code = 500
    def __init__(self, message="Internal processing error"):
        super().__init__(message)

class ConflictError(Exception):
    status_code = 409
    def __init__(self, message="Conflict error"):
        super().__init__(message)

class NotFoundError(Exception):
    status_code = 404
    def __init__(self, message="Not found error"):
        super().__init__(message)

class ForbiddenError(Exception):
    status_code = 403
    def __init__(self, message="Forbidden error"):
        super().__init__(message)


def register_error_handlers(app):
    @app.errorhandler(BadRequestError)
    def handle_bad_request(error):
        return jsonify({"message": str(error)}), error.status_code

    @app.errorhandler(InternalProcessingError)
    def handle_file_processing_error(error):
        return jsonify({"message": str(error)}), error.status_code
    
    @app.errorhandler(ConflictError)
    def handle_conflict_error(error):
        return jsonify({"message": str(error)}), error.status_code

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error):
        return jsonify({"message": str(error)}), error.status_code
        
    @app.errorhandler(ForbiddenError)
    def handle_forbidden_error(error):
        return jsonify({"message": str(error)}), error.status_code
    
