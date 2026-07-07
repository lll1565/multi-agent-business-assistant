"""Backend settings production flags."""

from backend.config.settings import BackendSettings, clear_backend_settings_cache, get_backend_settings


def test_production_flags(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("TRUSTED_HOSTS", "example.com, localhost")
    clear_backend_settings_cache()
    settings = get_backend_settings()
    assert settings.is_production is True
    assert settings.trusted_host_list == ["example.com", "localhost"]
    clear_backend_settings_cache()


def test_default_env_is_development() -> None:
    settings = BackendSettings()
    assert settings.is_production is False
    assert settings.chat_rate_limit_per_minute == 0
