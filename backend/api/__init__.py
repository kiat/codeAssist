import os
from flask import Flask
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate  # Import Migrate
from dotenv import load_dotenv

# Initialize extensions
ma = Marshmallow()
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class='config.Config'):
    # Create the Flask app instance
    app = Flask(__name__)

    # Load environment variables first so SECRET_KEY etc. are available
    load_dotenv()
    
    # Load the configuration (provides defaults like SECRET_KEY for test config)
    app.config.from_object(config_class)

    # SECRET_KEY must be set via env var or config class for session security.
    app.secret_key = os.environ.get('SECRET_KEY') or app.config.get('SECRET_KEY')
    if not app.secret_key:
        raise RuntimeError(
            "SECRET_KEY environment variable is required. "
            "Set it to a random secret string (e.g. python -c 'import secrets; print(secrets.token_hex(32))')."
        )
    
    # Initialize the extensions with the app
    # Lock CORS to the actual frontend origin to prevent CSRF on credentialed requests.
    # FRONTEND_ORIGIN must be set in production; defaults to localhost only for dev.
    frontend_origin = os.environ.get('FRONTEND_ORIGIN', 'http://localhost:3000')
    CORS(app, supports_credentials=True, origins=[frontend_origin])
    ma.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints and routes (do it after app is initialized)
    from routes import register_routes
    from util.errors import register_error_handlers

    register_routes(app)
    register_error_handlers(app)

    return app
