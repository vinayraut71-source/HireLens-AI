"""Recommendations module — schemas. PRD Section 8.5."""
from uuid import UUID
from pydantic import BaseModel

class RecommendationSignalResponse(BaseModel):
    id: UUID
    signal_type: str
    signal_key: str
    weight: float
    sample_count: int
    class Config: from_attributes = True

class RecommendedJobResponse(BaseModel):
    job_id: UUID
    title: str
    company: str | None = None
    location: str | None = None
    match_score: float
    reason: str | None = None
