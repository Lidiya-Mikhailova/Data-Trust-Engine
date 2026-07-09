from __future__ import annotations

from fastapi import APIRouter

from API.routes.health import router as health_router
from API.routes.sources import router as sources_router
from API.routes.etl import router as etl_router
from API.routes.trust import router as trust_router
from API.routes.decisions import router as decisions_router
from API.routes.data import router as data_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(sources_router, prefix="/sources", tags=["Sources"])
api_router.include_router(etl_router, prefix="/etl", tags=["ETL"])
api_router.include_router(trust_router, prefix="/trust", tags=["Trust"])
api_router.include_router(decisions_router, prefix="/decisions", tags=["Decisions"])
api_router.include_router(data_router, prefix="/data", tags=["Data"])
