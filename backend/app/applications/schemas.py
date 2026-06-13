"""Applications module — schemas. PRD Section 8.7 + 8.9."""
from uuid import UUID
from pydantic import BaseModel
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
