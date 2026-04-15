def test_login_api_returns_token(auth_session):
    assert auth_session.token
    assert auth_session.token_type == "Bearer"
    assert auth_session.email == "sysadmin@dhive.vn"
    assert auth_session.user_id == "11111111-1111-1111-1111-111111111111"