"""Unit tests for netcore_tac.api.settings."""

from pathlib import Path

import pytest

from netcore_tac.api.settings import ConfigurationError, Settings, load_settings

ENV_VARS = ["APP_NAME", "APP_ENV", "HOST", "PORT", "LOG_LEVEL", "MODEL_PATH",
            "MODEL_METADATA_PATH", "RATE_LIMIT_REQUESTS", "RATE_LIMIT_WINDOW_SECONDS",
            "RATE_LIMIT_BLOCK_SECONDS", "TRUST_PROXY_HEADERS", "DOCS_ENABLED"]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_defaults():
    s = load_settings(_env_file=None)
    assert s.app_name == "NetCore TAC ETA API"
    assert s.app_env == "development"
    assert (s.host, s.port, s.log_level) == ("0.0.0.0", 8000, "info")
    assert s.model_path == Path("models/eta_model.joblib")
    assert s.model_metadata_path == Path("models/eta_model.json")
    assert (s.rate_limit_requests, s.rate_limit_window_seconds, s.rate_limit_block_seconds) == (100, 60, 30)
    assert s.trust_proxy_headers is False and s.docs_enabled is True


def test_env_file_overrides(tmp_path):
    env = tmp_path / ".env"
    env.write_text("APP_ENV=Production\nPORT=9000\nLOG_LEVEL=DEBUG\nRATE_LIMIT_REQUESTS=5\n"
                   "TRUST_PROXY_HEADERS=true\nDOCS_ENABLED=false\nUNRELATED=1\n", encoding="utf-8")
    s = load_settings(_env_file=env)
    assert s.app_env == "production" and s.port == 9000 and s.log_level == "debug"
    assert s.rate_limit_requests == 5
    assert s.trust_proxy_headers is True and s.docs_enabled is False


def test_environment_beats_env_file(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("PORT=9000\n", encoding="utf-8")
    monkeypatch.setenv("PORT", "9100")
    assert load_settings(_env_file=env).port == 9100


@pytest.mark.parametrize("name,value", [
    ("PORT", "0"), ("PORT", "70000"), ("PORT", "abc"), ("APP_ENV", "staging"),
    ("LOG_LEVEL", "verbose"), ("RATE_LIMIT_REQUESTS", "0"), ("RATE_LIMIT_WINDOW_SECONDS", "-1"),
    ("RATE_LIMIT_BLOCK_SECONDS", "0"), ("DOCS_ENABLED", "maybe"), ("APP_NAME", ""),
])
def test_invalid_values_rejected_with_clear_message(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigurationError) as info:
        load_settings(_env_file=None)
    assert name in str(info.value)
    assert "Invalid configuration" in str(info.value)


def test_settings_class_direct_kwargs():
    assert Settings(_env_file=None, port=1234).port == 1234
