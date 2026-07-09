from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    next_page: Optional[int] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    uptime_seconds: float = 0.0


class SourceStateResponse(BaseModel):
    source_id: str
    state: str
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None


class SourceListResponse(BaseModel):
    sources: list[SourceStateResponse]


class ETLRunRequest(BaseModel):
    source_id: str
    mode: str = Field("full", pattern=r"^(full|incremental)$")


class ETLRunResponse(BaseModel):
    run_id: str
    source_id: str
    status: str
    records_processed: int = 0
    records_quarantined: int = 0


class ETLStatusResponse(BaseModel):
    run_id: str
    source_id: str
    status: str
    bronze_count: int = 0
    silver_count: int = 0
    gold_count: int = 0
    quarantine_count: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class TrustScoreResponse(BaseModel):
    source_id: str
    overall_score: float = Field(..., ge=0.0, le=1.0)
    quality_score: float = Field(..., ge=0.0, le=1.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    explanation: Optional[str] = None


class ReconciliationResponse(BaseModel):
    source_a: str
    source_b: str
    match_count: int
    mismatch_count: int
    match_rate: float = Field(..., ge=0.0, le=1.0)


class CircuitBreakerActionRequest(BaseModel):
    source_id: str
    action: str = Field(..., pattern=r"^(reset|trip)$")


class CircuitBreakerActionResponse(BaseModel):
    source_id: str
    state: str
    message: str


class DataQueryRequest(BaseModel):
    source_id: str
    layer: str = Field("gold", pattern=r"^(bronze|silver|gold)$")
    limit: int = Field(100, ge=1, le=10000)
    offset: int = Field(0, ge=0)


class DataQueryResponse(BaseModel):
    records: list[dict[str, Any]]
    total: int
    layer: str
    source_id: str
