from __future__ import annotations

from API.dependencies import get_settings


class TestGetSettings:
    def test_returns_settings_singleton(self):
        from Config import settings
        result = get_settings()
        assert result is settings

    def test_returns_app_settings_instance(self):
        from Config import AppSettings
        result = get_settings()
        assert isinstance(result, AppSettings)

    def test_works_without_request(self):
        result = get_settings(request=None)
        assert result is not None
