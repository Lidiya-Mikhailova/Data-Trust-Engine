from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from API.schemas import ETLRunRequest, ETLRunResponse, ETLStatusResponse, ErrorResponse

router = APIRouter()


@router.post(
    "/run",
    response_model=ETLRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_etl(body: ETLRunRequest):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="ETL execution not yet implemented",
    )


@router.get(
    "/runs/{run_id}",
    response_model=ETLStatusResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_etl_status(run_id: str):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"ETL run '{run_id}' not found",
    )
