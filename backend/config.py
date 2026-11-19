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

    CELERY = {
        "broker_url": os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
        "imports": ("routes.grading_tasks",),
        "task_ignore_result": True,
        "task_acks_late": True,
        "task_reject_on_worker_lost": True,
        "worker_prefetch_multiplier": 1,
        "broker_transport_options": {"visibility_timeout": 7200},
        "broker_connection_retry_on_startup": True,
        # Run by the `beat` service in docker-compose.yml.
        "beat_schedule": {
            "sweep-stuck-submissions": {
                "task": "grading.sweep_stuck_submissions",
                "schedule": float(os.getenv("GRADING_SWEEP_INTERVAL_SECONDS", "300")),
            },
        },
    }

    # How long a submission may stay running / pending before the sweep marks
    # it failed. Running includes waiting for the assignment container lock
    # behind another worker. Pending covers the queue during a deadline burst.
    GRADING_STUCK_RUNNING_SECONDS = int(os.getenv("GRADING_STUCK_RUNNING_SECONDS", "3600"))
    GRADING_STUCK_PENDING_SECONDS = int(os.getenv("GRADING_STUCK_PENDING_SECONDS", "7200"))

    # Limits for containers that run student code (see util/sandbox.py).
    # Network stays off unless an autograder really needs it at grading time;
    # setup.sh runs at image build time, which still has network.
    SANDBOX_NETWORK_DISABLED = os.getenv('SANDBOX_NETWORK_DISABLED', 'true').lower() == 'true'
    SANDBOX_MEM_LIMIT = os.getenv('SANDBOX_MEM_LIMIT', '512m')
    SANDBOX_JAVA_MEM_LIMIT = os.getenv('SANDBOX_JAVA_MEM_LIMIT', '1g')
    SANDBOX_CPUS = float(os.getenv('SANDBOX_CPUS', '1'))
    SANDBOX_PIDS_LIMIT = int(os.getenv('SANDBOX_PIDS_LIMIT', '256'))

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True
    SECRET_KEY = 'test-secret-key-for-testing'
    CELERY = {**Config.CELERY, "broker_url": "memory://"}
