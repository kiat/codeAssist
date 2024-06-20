from sqlalchemy import inspect
from api import db, app
from api.models import RegradeRequest

def create_regrade_requests_table():
    with app.app_context():
        inspector = inspect(db.engine)
        if not inspector.has_table("regrade_requests"):
            RegradeRequest.__table__.create(db.engine)
        else :
            print("dropping table")
            RegradeRequest.__table__.drop(db.engine)
            print("remaking table")
            RegradeRequest.__table__.create(db.engine)

if __name__ == "__main__":
    create_regrade_requests_table()
