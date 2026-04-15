from unittest.mock import Mock, patch

import pytest

from auth import AuthClient


@patch("auth.requests.post")
def test_login_success_parses_response(mock_post):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "token": "test-token-123",
        "tokenType": "Bearer",
        "expiresIn": 259200000,
        "username": "sysadmin",
        "email": "sysadmin@dhive.vn",
        "userId": "11111111-1111-1111-1111-111111111111",
        "roles": ["SYS_ADMIN"],
    }
    mock_post.return_value = mock_response

    client = AuthClient(
        base_url="http://example.com/api",
        login_endpoint="/v1/auth/login",
        email="sysadmin@dhive.vn",
        password="123456",
        timeout=30,
    )

    session = client.login()

    assert session.token == "test-token-123"
    assert session.token_type == "Bearer"
    assert session.username == "sysadmin"
    assert session.email == "sysadmin@dhive.vn"
    assert session.user_id == "11111111-1111-1111-1111-111111111111"


@patch("auth.requests.post")
def test_get_auth_header_returns_bearer_token(mock_post):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "token": "abc123",
        "tokenType": "Bearer",
        "expiresIn": 259200000,
        "username": "sysadmin",
        "email": "sysadmin@dhive.vn",
        "userId": "11111111-1111-1111-1111-111111111111",
        "roles": ["SYS_ADMIN"],
    }
    mock_post.return_value = mock_response

    client = AuthClient(
        base_url="http://example.com/api",
        login_endpoint="/v1/auth/login",
        email="sysadmin@dhive.vn",
        password="123456",
    )

    client.login()
    headers = client.get_auth_header()

    assert headers == {"Authorization": "Bearer abc123"}


def test_get_auth_header_raises_when_not_logged_in():
    client = AuthClient(
        base_url="http://example.com/api",
        login_endpoint="/v1/auth/login",
        email="sysadmin@dhive.vn",
        password="123456",
    )

    with pytest.raises(RuntimeError, match="No active auth session"):
        client.get_auth_header()


@patch("auth.requests.post")
def test_get_user_id_returns_user_id_from_session(mock_post):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "token": "abc123",
        "tokenType": "Bearer",
        "expiresIn": 259200000,
        "username": "sysadmin",
        "email": "sysadmin@dhive.vn",
        "userId": "11111111-1111-1111-1111-111111111111",
        "roles": ["SYS_ADMIN"],
    }
    mock_post.return_value = mock_response

    client = AuthClient(
        base_url="http://example.com/api",
        login_endpoint="/v1/auth/login",
        email="sysadmin@dhive.vn",
        password="123456",
    )

    client.login()

    assert client.get_user_id() == "11111111-1111-1111-1111-111111111111"