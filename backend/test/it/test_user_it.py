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

def test_user_login_integration(client):
    # First, create the user
    client.post('/create_user', json={
        "name": "Alice",
        "email_address": "alice@example.com",
        "password": "alice123",
        "eid": "EID456",
        "role": 1
    })

    # Then, attempt login
    response = client.post('/user_login', json={
        "email": "alice@example.com",
        "password": "alice123"
    })

    assert response.status_code == 200
    assert response.json["email_address"] == "alice@example.com"


def test_delete_user_integration(client):
    # First, create the user
    client.post('/create_user', json={
        "name": "Bob",
        "email_address": "bob@example.com",
        "password": "bob123",
        "eid": "EID789",
        "role": 1
    })

    # Delete the user
    response = client.delete('/delete_user', json={
        "eid": "EID789"
    })

    assert response.status_code == 200

def test_update_user_account_integration(client):
    # First, create the user
    client.post('/create_user', json={
        "name": "Charlie",
        "email_address": "charlie@example.com",
        "password": "charlie123",
        "eid": "EID999",
        "role": 1
    })

    # Update the user
    response = client.put('/update_account', json={
        "eid": "EID999",
        "new_name": "Charles",
        "new_password": "charles@example.com"
    })

    assert response.status_code == 200