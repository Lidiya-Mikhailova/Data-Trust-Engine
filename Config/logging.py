from pydantic import BaseModel, Field

from Config.defaults import LOG_LEVEL_DEFAULT, LOG_FORMAT_DEFAULT


class LogSettings(BaseModel):
    level: str = Field(LOG_LEVEL_DEFAULT, validation_alias="LOG_LEVEL")
    format: str = Field(LOG_FORMAT_DEFAULT, validation_alias="LOG_FORMAT")

    @property
    def structlog_config(self) -> dict:
        return {
            "level": self.level,
            "format": self.format,
        }
