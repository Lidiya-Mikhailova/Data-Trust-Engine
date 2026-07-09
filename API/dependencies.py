from __future__ import annotations

from fastapi import Request

from Config import AppSettings, settings


def get_settings(request: Request | None = None) -> AppSettings:
    return settings
