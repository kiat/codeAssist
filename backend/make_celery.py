from api import create_app

flask_app = create_app(config_class='config.Config')
celery_app = flask_app.extensions["celery"]
