from pydantic import BaseModel, Field

from Config.defaults import (
    MAX_RETRIES_DEFAULT,
    REQUEST_TIMEOUT_DEFAULT,
    VERIFY_SSL_DEFAULT,
)


class NetworkingSettings(BaseModel):
    request_timeout: int = Field(REQUEST_TIMEOUT_DEFAULT, validation_alias="REQUEST_TIMEOUT")
    max_retries: int = Field(MAX_RETRIES_DEFAULT, validation_alias="MAX_RETRIES")
    verify_ssl: bool = Field(VERIFY_SSL_DEFAULT, validation_alias="VERIFY_SSL")
