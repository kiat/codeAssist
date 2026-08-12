import pytest


@pytest.fixture
def login_as(client):
    def _login(user_id):
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
    return _login
