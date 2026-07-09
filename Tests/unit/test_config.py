from __future__ import annotations

from Config import AppSettings, LogSettings, S3Settings, BigQuerySettings


class TestAppSettings:
    def test_default_values(self):
        settings = AppSettings()
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000

    def test_custom_values(self):
        settings = AppSettings(API_HOST="127.0.0.1", API_PORT=9000)
        assert settings.api_host == "127.0.0.1"
        assert settings.api_port == 9000

    def test_nested_settings(self):
        settings = AppSettings()
        assert isinstance(settings.s3, S3Settings)
        assert isinstance(settings.bigquery, BigQuerySettings)
        assert isinstance(settings.logging, LogSettings)

    def test_logging_defaults(self):
        settings = AppSettings()
        assert settings.logging.level == "INFO"


class TestS3Settings:
    def test_default_paths(self):
        s3 = S3Settings()
        assert s3.bronze_path == "bronze"
        assert s3.silver_path == "silver"
        assert s3.gold_path == "gold"
        assert s3.quarantine_path == "quarantine"


class TestLogSettings:
    def test_structlog_config(self):
        log = LogSettings(LOG_LEVEL="DEBUG", LOG_FORMAT="json")
        cfg = log.structlog_config
        assert cfg["level"] == "DEBUG"
        assert cfg["format"] == "json"
