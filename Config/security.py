from pydantic import BaseModel, Field

from Config.defaults import SECRET_KEY_DEFAULT


class SecuritySettings(BaseModel):
    secret_key: str = Field(SECRET_KEY_DEFAULT, validation_alias="SECRET_KEY")
