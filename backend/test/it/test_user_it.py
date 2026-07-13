import uuid
import pytest
from flask import Flask
from api.models import db, User
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

@pytest.fixture
def admin_session(client, app):
    """Create an admin user and log them in for admin-only endpoints."""
    admin_id = str(uuid.uuid4())
    with app.app_context():
        admin = User(
            id=admin_id,
            name="Admin",
            email_address="admin@test.com",
            password="hashedpw",
            sis_user_id="ADMIN-EID",
            role="admin",
            coding_insights="No history.",
        )
        db.session.add(admin)
        db.session.commit()
    with client.session_transaction() as sess:
        sess["user_id"] = admin_id
    return admin_id

def test_user_creation_integration(client):
    """Test user creation via the actual API (integration test)."""
    payload = {"name": "John", "email_address": "john@example.com", "password": "password123", "eid": "EID123", "role": "student"}

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
        "role": "student"
    })

    # Then, attempt login
    response = client.post('/user_login', json={
        "email": "alice@example.com",
        "password": "alice123"
    })

    assert response.status_code == 200
    assert response.json["email_address"] == "alice@example.com"

def test_delete_user_integration(client, admin_session):
    # First, create the user
    response = client.post('/create_user', json={
        "name": "Bob",
        "email_address": "bob@example.com",
        "password": "bob123",
        "eid": "EID789",
        "role": "student"
    })
 
    assert response.status_code == 201 
 
    data = response.get_json() 
    user_id = data["id"]
 
    # Delete the user (admin session is active from fixture)
    response = client.delete('/delete_user', query_string={
        "id": user_id
    })
 
    assert response.status_code == 200

    # Confirm user is gone
    get_again = client.get('/get_user_by_id', query_string={
        "id": user_id
    })

    assert get_again.status_code == 404

def test_update_user_account_integration(client):
    # First, create the user
    response = client.post('/create_user', json={
        "name": "Charlie",
        "email_address": "charlie@example.com",
        "password": "charlie123",
        "eid": "EID999",
        "role": "student"
    })

    assert response.status_code == 201 

    data = response.get_json() 
    user_id = data["id"]

    # Update the user
    response = client.put('/update_account', json={
        "id": user_id, 
        "name": "Charles",
        "password": "charles123"
    })

    assert response.status_code == 200

    get_again = client.get('/get_user_by_id', query_string={
        "id": user_id
    })

    assert get_again.status_code == 200

    data = get_again.get_json() 
    assert data["name"] == "Charles" 
    #assert data["password"] == "charles123"

