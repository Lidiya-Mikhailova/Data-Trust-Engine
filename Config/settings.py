from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from Config.defaults import API_HOST_DEFAULT, API_PORT_DEFAULT, APP_ENV_DEFAULT, APP_VERSION_DEFAULT
from Config.logging import LogSettings
from Config.storage import BigQuerySettings, DataLakeSettings, S3Settings, SQLiteSettings


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

    s3: S3Settings = S3Settings()
    bigquery: BigQuerySettings = BigQuerySettings()
    sqlite: SQLiteSettings = SQLiteSettings()
    data_lake: DataLakeSettings = DataLakeSettings()
    logging: LogSettings = LogSettings()

    @classmethod
    def load(cls) -> "AppSettings":
        return cls()


settings = AppSettings.load()
