from sqlalchemy import Column, Boolean
from sqlalchemy import inspect
from sqlalchemy.schema import Table
from api import db, app

def add_is_reviewed_column():
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Check if the 'submissions' table exists
        if inspector.has_table("assignments"):
            # Reflect the existing table structure
            assignments_table = Table("assignments", db.metadata, autoload_with=db.engine)

            # Check if the 'is_reviewed' column exists
            if not hasattr(assignments_table.c, 'container_id'):
                # Add the 'is_reviewed' column with default value as False
                with db.engine.connect() as connection:
                    connection.execute('ALTER TABLE assignments ADD COLUMN container_id VARCHAR')
                    print("Column 'conatiner_id' added to 'assignments' table.")
            else:
                print("Column 'container_id' already exists in 'assignments' table.")
        else:
            print("Table 'assignments' does not exist.")

if __name__ == "__main__":
    add_is_reviewed_column()
