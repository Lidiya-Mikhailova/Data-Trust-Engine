from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from structlog import get_logger

from API.routes import api_router
from Config import settings

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup", extra={"api_host": settings.api_host, "api_port": settings.api_port})
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title="Data Trust Engine API",
    description="Production-grade platform for building reliable ETL pipelines with source failover and trust-based decision making",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
