from sqlalchemy import Column, Boolean
from sqlalchemy import inspect
from sqlalchemy.schema import Table
from api import db, app

def add_is_reviewed_column():
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Check if the 'submissions' table exists
        if inspector.has_table("submissions"):
            # Reflect the existing table structure
            submissions_table = Table("submissions", db.metadata, autoload_with=db.engine)

            # Check if the 'is_reviewed' column exists
            if not hasattr(submissions_table.c, 'default'):
                # Add the 'is_reviewed' column with default value as False
                with db.engine.connect() as connection:
                    connection.execute('ALTER TABLE submissions ADD COLUMN default BOOLEAN DEFAULT FALSE')
                    print("Column 'default' added to 'submissions' table.")
            else:
                print("Column 'default' already exists in 'submissions' table.")
        else:
            print("Table 'submissions' does not exist.")

if __name__ == "__main__":
    add_is_reviewed_column()
