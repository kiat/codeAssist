import importlib
import os

import pytest

import api as api_module
import config as config_module


def test_create_app_raises_when_secret_key_is_not_set(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        api_module.create_app(config_class="config.Config")


def test_create_app_accepts_secret_key_from_environment(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "env-provided-secret")

    app = api_module.create_app(config_class="config.Config")

    assert app.secret_key == "env-provided-secret"


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
