from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from API.schemas import (
    CircuitBreakerActionRequest,
    CircuitBreakerActionResponse,
    ErrorResponse,
)

router = APIRouter()


@router.get("/circuit-breaker/{source_id}", response_model=CircuitBreakerActionResponse)
async def get_circuit_breaker_state(source_id: str):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Circuit breaker state tracking not yet implemented",
    )


@router.post(
    "/circuit-breaker/{source_id}",
    response_model=CircuitBreakerActionResponse,
    responses={404: {"model": ErrorResponse}},
)
async def circuit_breaker_action(source_id: str, body: CircuitBreakerActionRequest):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Circuit breaker actions not yet implemented",
    )
