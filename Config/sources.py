from pydantic import BaseModel, Field

from Config.defaults import (
    PRIMARY_SOURCE_API_KEY_DEFAULT,
    PRIMARY_SOURCE_NAME_DEFAULT,
    PRIMARY_SOURCE_TYPE_DEFAULT,
    PRIMARY_SOURCE_URL_DEFAULT,
    SECOND_SOURCE_API_KEY_DEFAULT,
    SECOND_SOURCE_NAME_DEFAULT,
    SECOND_SOURCE_TYPE_DEFAULT,
    SECOND_SOURCE_URL_DEFAULT,
)


class PrimarySourceSettings(BaseModel):
    name: str = Field(PRIMARY_SOURCE_NAME_DEFAULT, validation_alias="PRIMARY_SOURCE_NAME")
    type: str = Field(PRIMARY_SOURCE_TYPE_DEFAULT, validation_alias="PRIMARY_SOURCE_TYPE")
    url: str = Field(PRIMARY_SOURCE_URL_DEFAULT, validation_alias="PRIMARY_SOURCE_URL")
    api_key: str = Field(PRIMARY_SOURCE_API_KEY_DEFAULT, validation_alias="PRIMARY_SOURCE_API_KEY")


class SecondSourceSettings(BaseModel):
    name: str = Field(SECOND_SOURCE_NAME_DEFAULT, validation_alias="SECOND_SOURCE_NAME")
    type: str = Field(SECOND_SOURCE_TYPE_DEFAULT, validation_alias="SECOND_SOURCE_TYPE")
    url: str = Field(SECOND_SOURCE_URL_DEFAULT, validation_alias="SECOND_SOURCE_URL")
    api_key: str = Field(SECOND_SOURCE_API_KEY_DEFAULT, validation_alias="SECOND_SOURCE_API_KEY")
