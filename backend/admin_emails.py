from app import app
from api import db
from api.models import AdminEmail

with app.app_context():
    db.create_all()  # Ensure all tables exist

# To add these emails, run the following commands in the terminal
# docker exec -it flask_container sh
# python admin_emails.py

emails = [
    "aw42679@utexas.edu",
    # Add more emails as needed
]

with app.app_context():
    # Remove emails not in the list
    AdminEmail.query.filter(~AdminEmail.email.in_(emails)).delete(synchronize_session=False)
    db.session.commit()

    # Add new emails if not already present
    for email in emails:
        if not AdminEmail.query.filter_by(email=email).first():
            admin = AdminEmail(email=email)
            db.session.add(admin)
    db.session.commit()
    print("Admin emails updated!")