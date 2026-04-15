import json
from datetime import timedelta

from utils import load_config, now_utc, random_wait_seconds, should_refresh_token


def test_random_wait_seconds_stays_in_range():
    min_seconds = 30
    max_seconds = 900

    for _ in range(100):
        value = random_wait_seconds(min_seconds, max_seconds)
        assert min_seconds <= value <= max_seconds


def test_should_refresh_token_returns_false_when_not_expired():
    token_created_at = now_utc() - timedelta(hours=10)
    refresh_after_hours = 48

    assert should_refresh_token(token_created_at, refresh_after_hours) is False


def test_should_refresh_token_returns_true_when_expired():
    token_created_at = now_utc() - timedelta(hours=50)
    refresh_after_hours = 48

    assert should_refresh_token(token_created_at, refresh_after_hours) is True


def test_load_config_reads_json_file(tmp_path):
    config_data = {
        "base_url": "http://example.com/api",
        "auth": {
            "email": "user@example.com",
            "password": "secret"
        }
    }

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    loaded = load_config(str(config_file))

    assert loaded["base_url"] == "http://example.com/api"
    assert loaded["auth"]["email"] == "user@example.com"
    assert loaded["auth"]["password"] == "secret"