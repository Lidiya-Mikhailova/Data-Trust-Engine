from pydantic import BaseModel, Field

from Config.defaults import (
    BRONZE_PATH_DEFAULT,
    DATA_LAKE_PATH_DEFAULT,
    GOLD_PATH_DEFAULT,
    QUARANTINE_PATH_DEFAULT,
    SILVER_PATH_DEFAULT,
)


class S3Settings(BaseModel):
    access_key_id: str = Field("", validation_alias="AWS_ACCESS_KEY_ID")
    secret_access_key: str = Field("", validation_alias="AWS_SECRET_ACCESS_KEY")
    region: str = Field("", validation_alias="AWS_REGION")
    bucket: str = Field("", validation_alias="S3_BUCKET")
    bronze_path: str = BRONZE_PATH_DEFAULT
    silver_path: str = SILVER_PATH_DEFAULT
    gold_path: str = GOLD_PATH_DEFAULT
    quarantine_path: str = QUARANTINE_PATH_DEFAULT


class BigQuerySettings(BaseModel):
    credentials_path: str = Field("", validation_alias="GOOGLE_APPLICATION_CREDENTIALS")
    project_id: str = Field("", validation_alias="GOOGLE_CLOUD_PROJECT")
    dataset: str = Field("", validation_alias="BIGQUERY_DATASET")


class SQLiteSettings(BaseModel):
    path: str = Field("./data/observability.db", validation_alias="SQLITE_PATH")


class DataLakeSettings(BaseModel):
    local_path: str = Field(DATA_LAKE_PATH_DEFAULT, validation_alias="DATA_LAKE_PATH")
    bronze_path: str = Field(BRONZE_PATH_DEFAULT, validation_alias="BRONZE_PATH")
    silver_path: str = Field(SILVER_PATH_DEFAULT, validation_alias="SILVER_PATH")
    gold_path: str = Field(GOLD_PATH_DEFAULT, validation_alias="GOLD_PATH")
    quarantine_path: str = Field(QUARANTINE_PATH_DEFAULT, validation_alias="QUARANTINE_PATH")
