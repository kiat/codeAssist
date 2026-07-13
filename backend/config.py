import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DB_CONNECTION_STRING')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    # Cross-domain deployments need SESSION_COOKIE_SAMESITE=None, which
    # browsers only accept together with SESSION_COOKIE_SECURE=true (HTTPS).
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    # If SameSite=None is configured explicitly and SECURE isn't set, default
    # SECURE to true rather than false: SameSite=None over plain HTTP is a
    # cross-site-readable session cookie, and browsers reject that
    # combination anyway, so defaulting false there only breaks sessions
    # silently instead of failing safely.
    _secure_env = os.getenv('SESSION_COOKIE_SECURE')
    if _secure_env is None:
        SESSION_COOKIE_SECURE = SESSION_COOKIE_SAMESITE == 'None'
    else:
        SESSION_COOKIE_SECURE = _secure_env.lower() == 'true'

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True
    SECRET_KEY = 'test-secret-key'