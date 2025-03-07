import pytest
from api import create_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(config_class="config.TestConfig")
    
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def mock_user_query(mocker):
    """Mock the database query for user lookup."""
    mock_query = mocker.patch("routes.user.db.session.query")
    mock_user_schema = mocker.patch("routes.user.UserSchema")
    return mock_query, mock_user_schema


# Test cases

def test_create_user_post(client, mocker):
    """Test the /create_user route."""
    
    mock_commit = mocker.patch("routes.user.db.session.commit")
    mock_add = mocker.patch("routes.user.db.session.add")
    mock_user_schema = mocker.patch("routes.user.UserSchema")

    mock_user_schema.return_value.dump.return_value = {"id": "123", "name": "John Doe"}

    payload = {
        "name": "John Doe",
        "password": "password123",
        "email_address": "john@example.com",
        "eid": "EID123",
        "role": 1,
    }

    response = client.post("/create_user", json=payload)

    assert response.status_code == 201
    assert response.json == {"id": "123", "name": "John Doe"}

    mock_commit.assert_called_once()
    mock_add.assert_called_once()


def test_user_login_success(client, mock_user_query, mocker):
    """Test the /user_login route with valid credentials."""
    mock_query, mock_user_schema = mock_user_query
    
    mock_user_schema.return_value.dump.return_value = {"id": "123", "name": "John Doe"}
    mock_query.return_value.filter_by.return_value.first.return_value = mock_user_schema.return_value.dump.return_value

    payload = {"email": "john@example.com", "password": "password123"}

    response = client.post("/user_login", json=payload)

    assert response.status_code == 200
    assert response.json == {"id": "123", "name": "John Doe"}
    mock_query.assert_called_once()


def test_user_login_failure(client, mock_user_query):
    """Test the /user_login route with invalid credentials."""
    mock_query, mock_user_schema = mock_user_query
    
    mock_user_schema.return_value.dump.return_value = []
    mock_query.return_value.filter_by.return_value.first.return_value = None

    payload = {"email": "invalid@example.com", "password": "wrongpassword"}

    response = client.post("/user_login", json=payload)

    assert response.status_code == 404
    assert response.data.decode() == "No user found"
    mock_query.assert_called_once()


def test_get_user_by_email_success(client, mocker, mock_user_query):
    """Test the /get_user_by_email route with a valid email."""
    mock_query, mock_user_schema = mock_user_query

    user_mock = mocker.Mock()
    user_mock.id = "123"
    user_mock.name = "John Doe"
    user_mock.email_address = "john@example.com"
    user_mock.role = 2
    mock_query.return_value.with_entities.return_value.filter_by.return_value.first.return_value = user_mock

    response = client.get("/get_user_by_email?email=john@example.com")

    assert response.status_code == 200
    assert response.json == {
        "id": "123",
        "name": "John Doe",
        "email_address": "john@example.com",
        "role": 2,
    }
    mock_query.assert_called_once()


def test_get_user_by_email_not_found(client, mock_user_query):
    """Test the /get_user_by_email route with an invalid email."""
    mock_query, mock_user_schema = mock_user_query
    mock_query.return_value.with_entities.return_value.filter_by.return_value.first.return_value = None

    response = client.get('/get_user_by_email?email=invalid@example.com')

    assert response.status_code == 404
    assert b'User not found' in response.data

    mock_query.assert_called_once()


def test_delete_user(client, mocker):
    """Test the /delete_user route."""
    mock_db = mocker.patch("routes.user.db")
    mock_filter = mocker.patch("routes.user.User.query")

    mock_filter.filter_by.return_value.delete.return_value = 1

    response = client.delete("/delete_user?id=123")

    assert response.status_code == 200
    assert response.data.decode() == "Success"

    mock_filter.filter_by.assert_called_once_with(id="123")
    mock_filter.filter_by.return_value.delete.assert_called_once()
    mock_db.session.commit.assert_called_once()


def test_update_account(client, mocker):
    """Test the /update_account route."""
    payload = {"id": "123", "name": "Updated Name", "password": None}
    
    user_mock = mocker.Mock()
    user_mock.id = "123"
    user_mock.name = "Old Name"
    user_mock.password = "oldpassword"
    
    mock_query = mocker.patch("routes.user.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = user_mock

    mock_commit = mocker.patch("routes.user.db.session.commit")
    
    response = client.put("/update_account", json=payload)
    
    assert response.status_code == 200
    assert response.json["message"] == "Account updated successfully"

    mock_query.assert_called_once()
    mock_query.return_value.filter_by.assert_called_once_with(id="123")
    mock_commit.assert_called_once()


# Edge cases to add in route implementations

# def test_create_user_missing_fields(client):
#     """Test creating a user with missing required fields."""
#     payload = {"name": "John Doe"}  # Missing 'password', 'email', etc.
    
#     response = client.post("/create_user", json=payload)

#     assert response.status_code == 400
#     assert b'Missing required fields' in response.data

# def test_user_login_missing_email(client):
#     """Test login with missing email."""
#     payload = {"password": "password123"}
    
#     response = client.post("/user_login", json=payload)

#     assert response.status_code == 400
#     assert b'Missing email' in response.data


# def test_user_login_missing_password(client):
#     """Test login with missing password."""
#     payload = {"email": "john@example.com"}
    
#     response = client.post("/user_login", json=payload)

#     assert response.status_code == 400
#     assert b'Missing password' in response.data
