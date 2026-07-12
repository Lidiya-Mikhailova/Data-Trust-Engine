from __future__ import annotations

from unittest.mock import patch

import pytest

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


class TestProductionValidation:
    def test_production_with_all_secrets(self):
        env = {
            "APP_ENV": "production",
            "SECRET_KEY": "sk-prod-123",
            "AWS_ACCESS_KEY_ID": "AKIA123",
            "AWS_SECRET_ACCESS_KEY": "secret123",
            "AWS_REGION": "us-east-1",
            "S3_BUCKET": "my-prod-bucket",
        }
        with patch.dict("os.environ", env, clear=False):
            settings = AppSettings.load()
        assert settings.app_env == "production"
        assert settings.security.secret_key == "sk-prod-123"
        assert settings.s3.access_key_id == "AKIA123"

    def test_production_missing_secrets_raises(self):
        env = {
            "APP_ENV": "production",
            "SECRET_KEY": "",
            "AWS_ACCESS_KEY_ID": "",
            "AWS_SECRET_ACCESS_KEY": "",
            "AWS_REGION": "",
            "S3_BUCKET": "",
        }
        with patch.dict("os.environ", env, clear=False):
            with pytest.raises(ValueError, match="Missing required configuration"):
                AppSettings.load()

    def test_production_partial_missing_secrets(self):
        env = {
            "APP_ENV": "production",
            "SECRET_KEY": "valid",
            "AWS_ACCESS_KEY_ID": "",
            "AWS_SECRET_ACCESS_KEY": "valid",
            "AWS_REGION": "us-east-1",
            "S3_BUCKET": "valid",
        }
        with patch.dict("os.environ", env, clear=False):
            with pytest.raises(ValueError, match="Missing required configuration"):
                AppSettings.load()


class TestBigQueryReexport:
    def test_bigquery_settings_reexport(self):
        from Config.bigquery import BigQuerySettings
        assert BigQuerySettings is not None
