import pytest
from api import create_app
import uuid

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

def test_create_user_success(client, mocker, mock_user_query):
    """Test the /create_user route."""

    mock_query, mock_user_schema = mock_user_query
    mock_commit = mocker.patch("routes.user.db.session.commit")
    mock_add = mocker.patch("routes.user.db.session.add")

    mock_user_schema.return_value.dump.return_value = {"id": "123", "name": "John Doe"}
    mock_query.return_value.filter_by.return_value.first.return_value = None

    payload = {
        "name": "John Doe",
        "password": "password123",
        "email_address": "john@example.com",
        "eid": "EID123",
        "role": "student",
    }

    response = client.post("/create_user", json=payload)

    assert response.status_code == 201
    assert response.json["id"] is not None
    assert response.json["name"] == "John Doe"

    mock_commit.assert_called_once()
    mock_add.assert_called_once()

    assert mock_query.return_value.filter_by.call_count == 2

def test_create_user_missing_fields(client):
    payload = {"name": "John Doe"}  # Missing 'password', 'email', etc.
    
    response = client.post("/create_user", json=payload)

    assert response.status_code == 400
    assert response.json["message"] == "Missing required fields"

def test_create_user_duplicate_eid(client, mock_user_query):
    """Test creating a user with a duplicate EID."""
    mock_query, _ = mock_user_query

    mock_query.return_value.fiter_by.return_value.first.side_effect = True
    
    payload = {
        "name": "John Doe",
        "password": "password123",
        "email_address": "example@email.com",
        "eid": "duplicate",
        "role": "student",
    }

    response = client.post("/create_user", json=payload)

    assert response.status_code == 409
    assert response.json["message"] == "EID already in use"

    mock_query.return_value.filter_by.assert_any_call(sis_user_id="duplicate")

def test_create_user_duplicate_email(client, mock_user_query):
    """Test creating a user with a duplicate email."""
    mock_query, _ = mock_user_query

    def filter_by_side_effect(**kwargs):
        if kwargs == {"sis_user_id": "EID123"}:
            return mock_query.return_value
        elif kwargs == {"email_address": "duplicate@email.com"}:
            return mock_query.return_value
        return None

    mock_query.return_value.filter_by.side_effect = filter_by_side_effect
    mock_query.return_value.first.side_effect = [None, True]

    payload = {
        "name": "John Doe",
        "password": "password123",
        "email_address": "duplicate@email.com",
        "eid": "EID123",
        "role": "student",
    }

    response = client.post("/create_user", json=payload)

    assert response.status_code == 409
    assert response.json["message"] == "Email already in use"

    mock_query.return_value.filter_by.assert_any_call(email_address="duplicate@email.com")
    mock_query.return_value.filter_by.assert_any_call(sis_user_id="EID123")


def test_user_login_success(client, mock_user_query, mocker):
    """Test the /user_login route with valid credentials."""
    mock_query, mock_user_schema = mock_user_query
    
    # our stubbed DB row must include the password so verify_password(...) returns True
    user_record = mocker.Mock()
    user_record.id = "123"
    user_record.name = "John Doe"
    user_record.password = "password123"
    # When we call UserSchema().dump(...) we still want only id/name in the JSON response
    mock_user_schema.return_value.dump.return_value = {"id": "123", "name": "John Doe"}
    mock_query.return_value.filter_by.return_value.first.return_value = user_record

    payload = {"email": "john@example.com", "password": "password123"}

    response = client.post("/user_login", json=payload)

    assert response.status_code == 200
    assert response.json["id"] == "123"
    assert response.json["name"] == "John Doe"
    mock_query.assert_called_once()


def test_user_login_failure(client, mock_user_query):
    """Test the /user_login route with invalid credentials."""
    mock_query, mock_user_schema = mock_user_query
    
    mock_user_schema.return_value.dump.return_value = []
    mock_query.return_value.filter_by.return_value.first.return_value = None

    payload = {"email": "invalid@example.com", "password": "wrongpassword"}

    response = client.post("/user_login", json=payload)

    assert response.status_code == 404
    mock_query.assert_called_once()

def test_user_login_missing_email(client):
    """Test login with missing email."""
    payload = {
                "password": "password123"
               }
    
    response = client.post("/user_login", json=payload)

    assert response.status_code == 400
    assert response.json["message"] == "Missing email or password"

def test_user_login_missing_password(client):
    """Test login with missing password."""
    payload = {
                "email": "example@email.com",
                }

    response = client.post("/user_login", json=payload)

    assert response.status_code == 400
    assert response.json["message"] == "Missing email or password"

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

    random_uuid = uuid.uuid4()
    user_mock = mocker.Mock() 
    user_mock.id = random_uuid
    
    mock_query = mocker.patch("routes.user.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = user_mock

    # Mock db.session.delete and commit
    mock_delete = mocker.patch("routes.user.db.session.delete")
    mock_commit = mocker.patch("routes.user.db.session.commit")

    response = client.delete("/delete_user", query_string={"id" : str(random_uuid)})

    assert response.status_code == 200
    assert response.data.decode() == "Success"

    # Check that filter_by was called with correct id
    mock_query.return_value.filter_by.assert_called_once_with(id=str(random_uuid))

    # Check that first() was called to fetch the user
    mock_query.return_value.filter_by.return_value.first.assert_called_once()

    # Check that delete was called with the mock user
    mock_delete.assert_called_once_with(user_mock)

    # Check that commit was called
    mock_commit.assert_called_once()


def test_delete_user_missing_id(client, mocker):
    """Test the /delete_user route."""


    response = client.delete("/delete_user")

    assert response.status_code == 400
    data = response.get_json() 
    assert data['message'] == "Missing User id"

def test_delete_user_invalid_id(client, mocker):
    """Test the /delete_user route."""


    response = client.delete("/delete_user", query_string={"id" : "123"})

    assert response.status_code == 400
    data = response.get_json() 
    assert data['message'] == "Invalid user id"

def test_delete_user_not_found(client, mocker):
    """Test the /delete_user route."""

    random_uuid = random_uuid = uuid.uuid4() 

    mock_query = mocker.patch("routes.user.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None


    response = client.delete("/delete_user", query_string={"id" : str(random_uuid)})

    assert response.status_code == 404
    data = response.get_json() 
    assert data['message'] == "User Not Found"

    mock_query.assert_called_once() 
    mock_query.return_value.filter_by.assert_called_once_with(id=str(random_uuid))


def test_delete_user_rolls_back_on_exception(client, mocker):
    random_uuid = uuid.uuid4()
    user_mock = mocker.Mock() 
    user_mock.id = random_uuid

    mock_session = mocker.patch("routes.user.db.session")

    
    mock_session.query.return_value.filter_by.return_value.first.return_value = user_mock

    mock_session.delete.return_value = None
    mock_session.commit.side_effect = Exception("Simulated DB failure")


    response = client.delete("/delete_user", query_string={"id" : str(random_uuid)})

    assert response.status_code == 500
    data = response.get_json()
    assert data["message"] == "Error deleting user"

    mock_session.rollback.assert_called_once()

def test_update_account(client, mocker):
    """Test the /update_account route."""

    random_uuid = uuid.uuid4()

    payload = {"id": str(random_uuid), "name": "Updated Name", "password": "Updated Password"}
    
    user_mock = mocker.Mock()
    user_mock.id = str(random_uuid)
    user_mock.name = "Old Name"
    user_mock.password = "oldpassword"
    
    mock_query = mocker.patch("routes.user.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = user_mock

    mock_commit = mocker.patch("routes.user.db.session.commit")
    
    response = client.put("/update_account", json=payload)
    
    assert response.status_code == 200
    assert response.json["message"] == "Account updated successfully"

    mock_query.assert_called_once()
    mock_query.return_value.filter_by.assert_called_once_with(id=str(random_uuid))
    mock_commit.assert_called_once()

def test_update_account_only_user(client, mocker):
    """Test the /update_account route."""

    random_uuid = uuid.uuid4()

    payload = {"id": str(random_uuid), "name": "Updated Name"}
    
    user_mock = mocker.Mock()
    user_mock.id = str(random_uuid)
    user_mock.name = "Old Name"
    user_mock.password = "oldpassword"
    
    mock_query = mocker.patch("routes.user.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = user_mock

    mock_commit = mocker.patch("routes.user.db.session.commit")
    
    response = client.put("/update_account", json=payload)
    
    assert response.status_code == 200
    assert response.json["message"] == "Account updated successfully"

    mock_query.assert_called_once()
    mock_query.return_value.filter_by.assert_called_once_with(id=str(random_uuid))
    mock_commit.assert_called_once()


def test_update_account_only_password(client, mocker):
    """Test the /update_account route."""

    random_uuid = uuid.uuid4()

    payload = {"id": str(random_uuid), "password": "Updated Password"}
    
    user_mock = mocker.Mock()
    user_mock.id = str(random_uuid)
    user_mock.name = "Old Name"
    user_mock.password = "oldpassword"
    
    mock_query = mocker.patch("routes.user.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = user_mock

    mock_commit = mocker.patch("routes.user.db.session.commit")
    
    response = client.put("/update_account", json=payload)
    
    assert response.status_code == 200
    assert response.json["message"] == "Account updated successfully"

    mock_query.assert_called_once()
    mock_query.return_value.filter_by.assert_called_once_with(id=str(random_uuid))
    mock_commit.assert_called_once()

def test_update_account_missing_id(client, mocker):
    """Test the /update_account route."""

    response = client.put("/update_account", json={})

    assert response.status_code == 400
    data = response.get_json() 
    assert data['message'] == "Missing user id"


def test_update_account_missing_user(client, mocker):
    """Test the /update_account route."""

    
    random_uuid = random_uuid = uuid.uuid4() 

    mock_query = mocker.patch("routes.user.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None


    response = client.put("/update_account", json={"id" : str(random_uuid)})

    assert response.status_code == 404
    data = response.get_json() 
    assert data['message'] == "User Not Found"

    mock_query.assert_called_once() 
    mock_query.return_value.filter_by.assert_called_once_with(id=str(random_uuid))

def test_update_user_rolls_back_on_exception(client, mocker):
    random_uuid = uuid.uuid4()
    user_mock = mocker.Mock() 
    user_mock.id = random_uuid

    payload = {"id": str(random_uuid), "password": "Updated Password"}

    mock_session = mocker.patch("routes.user.db.session")
    mock_session.query.return_value.filter_by.return_value.first.return_value = user_mock

    mock_session.commit.side_effect = Exception("Simulated DB failure")


    response = client.put("/update_account", json=payload)

    assert response.status_code == 500
    data = response.get_json()
    assert data["message"] == "Error updating account"

    mock_session.rollback.assert_called_once()




def test_get_user_by_id(client, mocker):
    """Test the /get_user_by_id route."""

    random_uuid = uuid.uuid4() 
    user_mock = mocker.Mock()
    user_mock.id = random_uuid
    user_mock.name = "Old Name"
    user_mock.password = "oldpassword"
    user_mock.coding_insights = "No history."
    user_mock.email_address =  "user@gmail.com"
    user_mock.role =  "student"
    user_mock.sis_user_id = "123"


    mock_query = mocker.patch("routes.user.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = user_mock

    response = client.get("/get_user_by_id", query_string={"id": str(random_uuid)})

    assert response.status_code == 200
    assert response.json == {
        "id" : str(random_uuid),
        "name": "Old Name",
        "password": "oldpassword",
        "coding_insights": "No history.",
        "email_address":  "user@gmail.com",
        "role":  "student",
        "sis_user_id": "123"
    }

    mock_query.assert_called_once() 
    mock_query.return_value.filter_by.assert_called_once_with(id=str(random_uuid))


def test_get_user_by_id_not_found(client, mocker):
    """Test the /get_user_by_id route."""

    random_uuid = uuid.uuid4() 

    mock_query = mocker.patch("routes.user.db.session.query")
    mock_query.return_value.filter_by.return_value.first.return_value = None

    response = client.get("/get_user_by_id", query_string={"id": str(random_uuid)})

    assert response.status_code == 404
    data = response.get_json() 
    assert data['message'] == "User does not exist"

    mock_query.assert_called_once() 
    mock_query.return_value.filter_by.assert_called_once_with(id=str(random_uuid))


def test_get_user_by_id_missing_id(client, mocker):
    """Test the /get_user_by_id route."""

    response = client.get("/get_user_by_id")

    assert response.status_code == 400
    data = response.get_json() 
    assert data['message'] == "Missing user id"



def test_get_user_by_id_non_uuid(client, mocker):
    """Test the /get_user_by_id route."""

    response = client.get("/get_user_by_id", query_string={"id" : "123"})

    assert response.status_code == 400
    data = response.get_json() 
    assert data['message'] == "Invalid user id"


    




    

