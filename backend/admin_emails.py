from app import app
from api import db
from api.models import AdminEmail

emails = [
    "admin1@example.com",
    "admin2@example.com",
    # Add more emails as needed
]

with app.app_context():
    for email in emails:
        if not AdminEmail.query.filter_by(email=email).first():
            admin = AdminEmail(email=email)
            db.session.add(admin)
    db.session.commit()
    print("Admin emails added!")