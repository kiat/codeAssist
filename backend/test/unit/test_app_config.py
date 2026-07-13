import importlib
import os
import stat

import pytest

import api as api_module
import config as config_module


def test_get_or_create_fallback_secret_key_creates_key_with_owner_only_permissions(tmp_path, monkeypatch):
    key_path = tmp_path / ".flask_secret_key"
    monkeypatch.setattr(api_module, "_FALLBACK_SECRET_KEY_PATH", str(key_path))

    key = api_module._get_or_create_fallback_secret_key()

    assert key_path.read_text().strip() == key
    assert stat.S_IMODE(key_path.stat().st_mode) == 0o600


def test_get_or_create_fallback_secret_key_reuses_persisted_key(tmp_path, monkeypatch):
    key_path = tmp_path / ".flask_secret_key"
    monkeypatch.setattr(api_module, "_FALLBACK_SECRET_KEY_PATH", str(key_path))

    first = api_module._get_or_create_fallback_secret_key()
    second = api_module._get_or_create_fallback_secret_key()

    assert first == second


def test_get_or_create_fallback_secret_key_handles_concurrent_creation_race(tmp_path, monkeypatch):
    key_path = tmp_path / ".flask_secret_key"
    monkeypatch.setattr(api_module, "_FALLBACK_SECRET_KEY_PATH", str(key_path))

    original_open = os.open

    def _open_wins_race(path, flags, mode=0o777):
        if path == str(key_path) and flags & os.O_EXCL:
            # Simulate a second process creating the file first, between
            # our initial "does it exist" read and our own os.open call.
            with open(path, "w") as f:
                f.write("winner-key")
            raise FileExistsError()
        return original_open(path, flags, mode)

    monkeypatch.setattr(os, "open", _open_wins_race)

    key = api_module._get_or_create_fallback_secret_key()

    assert key == "winner-key"


@pytest.fixture
def reloaded_config():
    tracked_vars = ("SESSION_COOKIE_SAMESITE", "SESSION_COOKIE_SECURE")
    original_env = {key: os.environ.get(key) for key in tracked_vars}

    def _reload(**env):
        for key in tracked_vars:
            os.environ.pop(key, None)
        os.environ.update(env)
        importlib.reload(config_module)
        return config_module.Config

    yield _reload

    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    importlib.reload(config_module)


def test_session_cookie_secure_defaults_true_when_samesite_none(reloaded_config):
    Config = reloaded_config(SESSION_COOKIE_SAMESITE="None")
    assert Config.SESSION_COOKIE_SECURE is True


def test_session_cookie_secure_defaults_false_when_samesite_lax(reloaded_config):
    Config = reloaded_config()
    assert Config.SESSION_COOKIE_SECURE is False


def test_session_cookie_secure_respects_explicit_env_override(reloaded_config):
    Config = reloaded_config(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE="false")
    assert Config.SESSION_COOKIE_SECURE is False
