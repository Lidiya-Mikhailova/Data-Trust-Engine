import os

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from Config.ai import AISettings
from Config.circuit_breaker import CircuitBreakerSettings
from Config.dagster import DagsterSettings, DagsterPostgresSettings
from Config.defaults import API_HOST_DEFAULT, API_PORT_DEFAULT, APP_ENV_DEFAULT, APP_VERSION_DEFAULT
from Config.logging import LogSettings
from Config.networking import NetworkingSettings
from Config.security import SecuritySettings
from Config.sources import PrimarySourceSettings, SecondSourceSettings
from Config.storage import BigQuerySettings, DataLakeSettings, S3Settings, SQLiteSettings

_PRODUCTION = "production"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = Field(APP_ENV_DEFAULT, validation_alias="APP_ENV")
    app_version: str = Field(APP_VERSION_DEFAULT, validation_alias="APP_VERSION")

    api_host: str = Field(API_HOST_DEFAULT, validation_alias="API_HOST")
    api_port: int = Field(API_PORT_DEFAULT, validation_alias="API_PORT")

    logging: LogSettings = LogSettings()
    data_lake: DataLakeSettings = DataLakeSettings()
    sqlite: SQLiteSettings = SQLiteSettings()
    s3: S3Settings = S3Settings()
    bigquery: BigQuerySettings = BigQuerySettings()

    primary_source: PrimarySourceSettings = PrimarySourceSettings()
    second_source: SecondSourceSettings = SecondSourceSettings()
    networking: NetworkingSettings = NetworkingSettings()
    circuit_breaker: CircuitBreakerSettings = CircuitBreakerSettings()
    dagster: DagsterSettings = DagsterSettings()
    ai: AISettings = AISettings()
    security: SecuritySettings = SecuritySettings()

    @model_validator(mode="after")
    def _inject_env_vars(self) -> "AppSettings":
        env = os.environ

        self.logging = LogSettings(
            LOG_LEVEL=env.get("LOG_LEVEL", self.logging.level),
            LOG_FORMAT=env.get("LOG_FORMAT", self.logging.format),
        )

        self.data_lake = DataLakeSettings(
            DATA_LAKE_PATH=env.get("DATA_LAKE_PATH", self.data_lake.local_path),
            BRONZE_PATH=env.get("BRONZE_PATH", self.data_lake.bronze_path),
            SILVER_PATH=env.get("SILVER_PATH", self.data_lake.silver_path),
            GOLD_PATH=env.get("GOLD_PATH", self.data_lake.gold_path),
            QUARANTINE_PATH=env.get("QUARANTINE_PATH", self.data_lake.quarantine_path),
        )

        self.sqlite = SQLiteSettings(
            SQLITE_PATH=env.get("SQLITE_PATH", self.sqlite.path),
        )

        self.s3 = S3Settings(
            AWS_ACCESS_KEY_ID=env.get("AWS_ACCESS_KEY_ID", self.s3.access_key_id),
            AWS_SECRET_ACCESS_KEY=env.get("AWS_SECRET_ACCESS_KEY", self.s3.secret_access_key),
            AWS_REGION=env.get("AWS_REGION", self.s3.region),
            S3_BUCKET=env.get("S3_BUCKET", self.s3.bucket),
        )

        self.bigquery = BigQuerySettings(
            GOOGLE_APPLICATION_CREDENTIALS=env.get("GOOGLE_APPLICATION_CREDENTIALS", self.bigquery.credentials_path),
            GOOGLE_CLOUD_PROJECT=env.get("GOOGLE_CLOUD_PROJECT", self.bigquery.project_id),
            BIGQUERY_DATASET=env.get("BIGQUERY_DATASET", self.bigquery.dataset),
        )

        self.primary_source = PrimarySourceSettings(
            PRIMARY_SOURCE_NAME=env.get("PRIMARY_SOURCE_NAME", self.primary_source.name),
            PRIMARY_SOURCE_TYPE=env.get("PRIMARY_SOURCE_TYPE", self.primary_source.type),
            PRIMARY_SOURCE_URL=env.get("PRIMARY_SOURCE_URL", self.primary_source.url),
            PRIMARY_SOURCE_API_KEY=env.get("PRIMARY_SOURCE_API_KEY", self.primary_source.api_key),
        )

        self.second_source = SecondSourceSettings(
            SECOND_SOURCE_NAME=env.get("SECOND_SOURCE_NAME", self.second_source.name),
            SECOND_SOURCE_TYPE=env.get("SECOND_SOURCE_TYPE", self.second_source.type),
            SECOND_SOURCE_URL=env.get("SECOND_SOURCE_URL", self.second_source.url),
            SECOND_SOURCE_API_KEY=env.get("SECOND_SOURCE_API_KEY", self.second_source.api_key),
        )

        self.networking = NetworkingSettings(
            REQUEST_TIMEOUT=int(env.get("REQUEST_TIMEOUT", self.networking.request_timeout)),
            MAX_RETRIES=int(env.get("MAX_RETRIES", self.networking.max_retries)),
            VERIFY_SSL=env.get("VERIFY_SSL", str(self.networking.verify_ssl)).lower() == "true",
        )

        self.circuit_breaker = CircuitBreakerSettings(
            CIRCUIT_BREAKER_FAILURE_THRESHOLD=int(env.get("CIRCUIT_BREAKER_FAILURE_THRESHOLD", self.circuit_breaker.failure_threshold)),
            CIRCUIT_BREAKER_SUCCESS_THRESHOLD=int(env.get("CIRCUIT_BREAKER_SUCCESS_THRESHOLD", self.circuit_breaker.success_threshold)),
            CIRCUIT_BREAKER_TIMEOUT=int(env.get("CIRCUIT_BREAKER_TIMEOUT", self.circuit_breaker.timeout)),
            TRUST_SCORE_THRESHOLD=float(env.get("TRUST_SCORE_THRESHOLD", self.circuit_breaker.trust_score_threshold)),
            ALLOW_SOURCE_FAILOVER=env.get("ALLOW_SOURCE_FAILOVER", str(self.circuit_breaker.allow_source_failover)).lower() == "true",
        )

        self.dagster = DagsterSettings(
            postgres=DagsterPostgresSettings(
                DAGSTER_POSTGRES_HOST=env.get("DAGSTER_POSTGRES_HOST", self.dagster.postgres.host),
                DAGSTER_POSTGRES_PORT=int(env.get("DAGSTER_POSTGRES_PORT", self.dagster.postgres.port)),
                DAGSTER_POSTGRES_USER=env.get("DAGSTER_POSTGRES_USER", self.dagster.postgres.user),
                DAGSTER_POSTGRES_PASSWORD=env.get("DAGSTER_POSTGRES_PASSWORD", self.dagster.postgres.password),
                DAGSTER_POSTGRES_DB=env.get("DAGSTER_POSTGRES_DB", self.dagster.postgres.db),
                DAGSTER_POSTGRES_EXPORT_PORT=int(env.get("DAGSTER_POSTGRES_EXPORT_PORT", self.dagster.postgres.export_port)),
            ),
            DAGSTER_WEBSERVER_PORT=int(env.get("DAGSTER_WEBSERVER_PORT", self.dagster.webserver_port)),
            DAGSTER_HOME=env.get("DAGSTER_HOME", self.dagster.home),
        )

        self.ai = AISettings(
            OPENAI_API_KEY=env.get("OPENAI_API_KEY", self.ai.openai_api_key),
        )

        self.security = SecuritySettings(
            SECRET_KEY=env.get("SECRET_KEY", self.security.secret_key),
        )

        return self

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "AppSettings":
        if self.app_env != _PRODUCTION:
            return self

        required_secrets: list[tuple[str, str]] = [
            ("security.secret_key", self.security.secret_key),
            ("s3.access_key_id", self.s3.access_key_id),
            ("s3.secret_access_key", self.s3.secret_access_key),
            ("s3.region", self.s3.region),
            ("s3.bucket", self.s3.bucket),
        ]

        missing = [name for name, value in required_secrets if not value]
        if missing:
            missing_list = ", ".join(missing)
            raise ValueError(
                f"Missing required configuration for production: {missing_list}. "
                "Set these environment variables before starting the application."
            )

        return self

    @classmethod
    def load(cls) -> "AppSettings":
        return cls()


settings = AppSettings.load()
