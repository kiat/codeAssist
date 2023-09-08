from autograder_models import db, app

# Create Postgres tables
def create_tables():
    with app.app_context():
        db.drop_all()
        db.create_all()

create_tables()