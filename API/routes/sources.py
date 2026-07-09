from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from API.schemas import ErrorResponse, SourceListResponse, SourceStateResponse

router = APIRouter()


@router.get("", response_model=SourceListResponse)
async def list_sources():
    return SourceListResponse(sources=[])


@router.get(
    "/{source_id}",
    response_model=SourceStateResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_source_state(source_id: str):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Source '{source_id}' not found",
    )
