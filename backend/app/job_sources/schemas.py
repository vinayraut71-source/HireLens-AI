"""
Pydantic schemas for External Job Ingestion.
Sprint 12: Ingestion layer.
"""
from datetime import datetime
from uuid import UUID
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


class ProviderResponse(BaseModel):
    name: str
    enabled: bool


class ProviderHealthSummary(BaseModel):
    provider_name: str
    status: str
    last_successful_sync: datetime | None = None
    failure_count: int
    success_rate: float
    avg_duration_seconds: float


class SyncLogResponse(BaseModel):
    id: UUID | None = None
    provider_name: str
    sync_started_at: datetime
    sync_completed_at: datetime | None = None
    jobs_received: int = 0
    jobs_created: int = 0
    jobs_updated: int = 0
    jobs_expired: int = 0
    status: str
    error_message: str | None = None

    class Config:
        from_attributes = True


class ProviderConfigUpdate(BaseModel):
    enabled: bool | None = None
    sync_interval_minutes: int | None = None
    rate_limit_per_hour: int | None = None
    retry_limit: int | None = None
    timeout_seconds: int | None = None
    max_concurrent_jobs: int | None = None


class ProviderConfigResponse(BaseModel):
    provider_name: str
    enabled: bool
    sync_interval_minutes: int
    rate_limit_per_hour: int
    retry_limit: int
    timeout_seconds: int
    max_concurrent_jobs: int

    class Config:
        from_attributes = True


class FailedSyncJobResponse(BaseModel):
    id: UUID
    provider_name: str
    payload: dict
    error_message: str | None = None
    retry_count: int
    resolved: bool
    resolved_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True

