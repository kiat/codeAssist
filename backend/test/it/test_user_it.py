import pytest
from flask import Flask
from api.models import db
from routes.user import user
from api import create_app

@pytest.fixture
def app():
    """Create an app instance for testing."""
    app = create_app(config_class="config.TestConfig")

    with app.app_context():
        db.create_all()  
        yield app
        db.drop_all()  

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

def test_user_creation_integration(client):
    """Test user creation via the actual API (integration test)."""
    payload = {"name": "John", "email_address": "john@example.com", "password": "password123", "eid": "EID123", "role": 1}

    response = client.post('/create_user', json=payload)

    assert response.status_code == 201
    assert response.json["name"] == "John"
    assert response.json["email_address"] == "john@example.com"
