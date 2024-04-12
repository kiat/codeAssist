from autograder_models import db
from sqlalchemy import text

def drop_tables_with_cascade():
    try:
        db.session.execute(text("DROP TABLE IF EXISTS test_case_results CASCADE;"))
        db.session.execute(text("DROP TABLE IF EXISTS submissions CASCADE;"))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error dropping tables: {e}")

def create_tables():
    drop_tables_with_cascade()  # Ensure dependent tables are dropped first
    db.create_all()

if __name__ == "__main__":
    create_tables()
