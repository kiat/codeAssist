import sys
from app import app
from api import db
from api.models import AdminEmail

#To add emails, run the following commands in terminal
#docker exec -it flask_container sh
#python admin_emails.py your_email@example.com

with app.app_context():
    db.create_all()  # Ensure all tables exist

if len(sys.argv) < 2:
    print("Usage: python admin_emails.py email1@example.com") #correct usage if no email provided
    sys.exit(1)

email_args = sys.argv[1:]

with app.app_context():
    for email_arg in email_args:
        if not AdminEmail.query.filter_by(email=email_arg).first():
            admin = AdminEmail(email=email_arg)
            db.session.add(admin)
            print(f"Admin email '{email_arg}' added.")
        else:
            print(f"Admin email '{email_arg}' already exists.")
    db.session.commit()