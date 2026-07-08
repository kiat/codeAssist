import os
import secrets
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

_FALLBACK_SECRET_KEY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.flask_secret_key'
)


def _get_or_create_fallback_secret_key():
    """Reads a persisted fallback key, or creates one on first use.

    A pure per-process random key breaks session validation across
    co-located worker processes (e.g. gunicorn --workers N), since each
    process would sign cookies with a different key. Persisting it to a
    local file lets processes on the same host share one.

    This only covers processes sharing one filesystem. It does not help
    across multiple hosts, replicas, or containers with separate
    filesystems and no shared volume; those deployments still need
    SECRET_KEY set explicitly in the environment.
    """
    try:
        with open(_FALLBACK_SECRET_KEY_PATH, 'r') as f:
            key = f.read().strip()
            if key:
                return key
    except FileNotFoundError:
        pass

    new_key = secrets.token_hex(32)
    try:
        fd = os.open(_FALLBACK_SECRET_KEY_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY, mode=0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(new_key)
        return new_key
    except FileExistsError:
        # Another process won the race to create the file; use its value.
        with open(_FALLBACK_SECRET_KEY_PATH, 'r') as f:
            return f.read().strip()


def create_app(config_class='config.Config'):
    # Create the Flask app instance
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')
    if not app.secret_key:
        app.secret_key = _get_or_create_fallback_secret_key()
        app.logger.warning(
            "SECRET_KEY environment variable not set; using a fallback key "
            "persisted to %s. Set SECRET_KEY in the environment for "
            "production deployments.",
            _FALLBACK_SECRET_KEY_PATH,
        )

    # Load environment variables
    load_dotenv()

    # Load the configuration
    app.config.from_object(config_class)

    # Initialize the extensions with the app
    frontend_origin = os.getenv('FRONTEND_URL', 'http://localhost:3000')
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
