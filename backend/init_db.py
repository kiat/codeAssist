from api import db, create_app
from api.models import *

app = create_app()

# Create Postgres tables
def create_tables():
    with app.app_context():
        db.drop_all()
        db.create_all()

create_tables()