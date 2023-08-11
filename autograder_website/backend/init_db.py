from autograder_app import app, db
from autograder_models import *

# Create Postgres tables
def create_tables():
    with app.app_context():
        db.drop_all()
        db.create_all()

create_tables()