from pydantic import BaseModel, Field

from Config.defaults import OPENAI_API_KEY_DEFAULT


class AISettings(BaseModel):
    openai_api_key: str = Field(OPENAI_API_KEY_DEFAULT, validation_alias="OPENAI_API_KEY")
