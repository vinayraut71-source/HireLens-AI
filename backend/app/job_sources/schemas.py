"""
Pydantic schemas for External Job Ingestion.
Sprint 12: Ingestion layer.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    source: str | None = Field(
        default=None, 
        description="Specific source name to ingest (e.g. 'linkedin'). If null, ingests all sources."
    )


class IngestionResponse(BaseModel):
    status: str
    processed_count: int
    new_count: int
    updated_count: int
    duration_seconds: float


class SourceStatsResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    expired_jobs: int
    archived_jobs: int
    sources: dict[str, int]


class JobSourceResponse(BaseModel):
    name: str
    enabled: bool
    last_ingested_at: datetime | None = None
