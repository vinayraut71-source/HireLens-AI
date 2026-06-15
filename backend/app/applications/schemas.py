"""Applications module — schemas. PRD Section 8.7 + 8.9 + Sprint 8."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class ApplicationCreateRequest(BaseModel): company: str; position: str; job_id: UUID | None = None; version_id: UUID | None = None; job_url: str | None = None; notes: str | None = None
class ApplicationResponse(BaseModel):
    id: UUID; company: str; position: str; status: str; match_score: float | None = None; applied_date: str | None = None
    class Config: from_attributes = True
class ApplicationUpdateRequest(BaseModel): status: str | None = None; notes: str | None = None; follow_up_date: str | None = None
class ApplicationStatsResponse(BaseModel): total: int = 0; by_status: dict = {}
class OutcomeCreateRequest(BaseModel): event_type: str; metadata: dict = {}
class PackageResponse(BaseModel):
    id: UUID; approval_status: str; match_score: float; cover_letter: str | None = None
    class Config: from_attributes = True


# --- Job Application tracking schemas (Sprint 8) ---

class JobApplicationCreateRequest(BaseModel):
    job_id: UUID
    resume_version_id: UUID
    status: str = "draft"  # draft, saved, applied, etc.
    source: str | None = None
    notes: str | None = None


class JobSnapshotResponse(BaseModel):
    title: str
    company: str | None = None
    location: str | None = None
    salary: str | None = None
    url: str | None = None


class JobApplicationResponse(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    resume_version_id: UUID
    status: str
    outcome_type: str
    job_snapshot: JobSnapshotResponse | None
    source: str | None
    notes: str | None
    applied_at: datetime | None
    first_response_at: datetime | None
    interview_at: datetime | None
    offer_at: datetime | None
    rejection_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobApplicationStatusUpdateRequest(BaseModel):
    status: str
    notes: str | None = None
    outcome_type: str | None = None


class ApplicationTimelineEventResponse(BaseModel):
    id: UUID
    application_id: UUID
    event_type: str
    previous_status: str | None
    new_status: str
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True

