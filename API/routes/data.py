from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from API.schemas import DataQueryRequest, DataQueryResponse, ErrorResponse

router = APIRouter()


@router.post(
    "/query",
    response_model=DataQueryResponse,
    responses={404: {"model": ErrorResponse}},
)
async def query_data(body: DataQueryRequest):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Data querying not yet implemented",
    )
