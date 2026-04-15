import json
from pathlib import Path

import pytest

from auth import AuthClient
from stream_api import StreamApiClient


@pytest.fixture(scope="session")
def test_config():
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "config.test.json"

    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="session")
def auth_client(test_config):
    return AuthClient(
        base_url=test_config["base_url"],
        login_endpoint=test_config["endpoints"]["login"],
        email=test_config["auth"]["email"],
        password=test_config["auth"]["password"],
        timeout=30,
    )


@pytest.fixture(scope="session")
def stream_client(test_config):
    return StreamApiClient(
        base_url=test_config["base_url"],
        endpoints=test_config["endpoints"],
        timeout=30,
    )


@pytest.fixture(scope="session")
def auth_session(auth_client):
    return auth_client.login()


@pytest.fixture(scope="session")
def auth_headers(auth_client, auth_session):
    return auth_client.get_auth_header()