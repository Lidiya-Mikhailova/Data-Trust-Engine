from pydantic import BaseModel, Field

from Config.defaults import (
    DAGSTER_HOME_DEFAULT,
    DAGSTER_POSTGRES_DB_DEFAULT,
    DAGSTER_POSTGRES_EXPORT_PORT_DEFAULT,
    DAGSTER_POSTGRES_HOST_DEFAULT,
    DAGSTER_POSTGRES_PASSWORD_DEFAULT,
    DAGSTER_POSTGRES_PORT_DEFAULT,
    DAGSTER_POSTGRES_USER_DEFAULT,
    DAGSTER_WEBSERVER_PORT_DEFAULT,
)


class DagsterPostgresSettings(BaseModel):
    host: str = Field(DAGSTER_POSTGRES_HOST_DEFAULT, validation_alias="DAGSTER_POSTGRES_HOST")
    port: int = Field(DAGSTER_POSTGRES_PORT_DEFAULT, validation_alias="DAGSTER_POSTGRES_PORT")
    user: str = Field(DAGSTER_POSTGRES_USER_DEFAULT, validation_alias="DAGSTER_POSTGRES_USER")
    password: str = Field(DAGSTER_POSTGRES_PASSWORD_DEFAULT, validation_alias="DAGSTER_POSTGRES_PASSWORD")
    db: str = Field(DAGSTER_POSTGRES_DB_DEFAULT, validation_alias="DAGSTER_POSTGRES_DB")
    export_port: int = Field(DAGSTER_POSTGRES_EXPORT_PORT_DEFAULT, validation_alias="DAGSTER_POSTGRES_EXPORT_PORT")


class DagsterSettings(BaseModel):
    postgres: DagsterPostgresSettings = DagsterPostgresSettings()
    webserver_port: int = Field(DAGSTER_WEBSERVER_PORT_DEFAULT, validation_alias="DAGSTER_WEBSERVER_PORT")
    home: str = Field(DAGSTER_HOME_DEFAULT, validation_alias="DAGSTER_HOME")
