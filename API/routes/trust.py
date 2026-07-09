from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from API.schemas import (
    ErrorResponse,
    ReconciliationResponse,
    TrustScoreResponse,
)

router = APIRouter()


@router.get(
    "/score/{source_id}",
    response_model=TrustScoreResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_trust_score(source_id: str):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Trust score computation not yet implemented",
    )


@router.get(
    "/reconciliation/{source_a}/{source_b}",
    response_model=ReconciliationResponse,
    responses={404: {"model": ErrorResponse}},
)
async def reconcile_sources(source_a: str, source_b: str):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Reconciliation not yet implemented",
    )
