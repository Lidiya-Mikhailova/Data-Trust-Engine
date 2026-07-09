from __future__ import annotations

import time

from fastapi import APIRouter

from API.schemas import HealthResponse

router = APIRouter()

_start_time: float = time.time()


@router.get("", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        version="0.1.0",
        uptime_seconds=time.time() - _start_time,
    )
