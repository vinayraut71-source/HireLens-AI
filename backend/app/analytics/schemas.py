"""Analytics module — Pydantic schemas. PRD Section 8.8."""
from datetime import date
from uuid import UUID
from pydantic import BaseModel

class AnalyticsSnapshotResponse(BaseModel):
    id: UUID
    snapshot_date: date
    total_applications: int
    applications_this_month: int
    interview_rate: float | None = None
    rejection_rate: float | None = None
    offer_rate: float | None = None
    avg_match_score: float | None = None
    avg_ats_score: float | None = None
    ats_improvement: int | None = None
    skills_completed: int
    class Config: from_attributes = True

class AnalyticsTimeSeriesResponse(BaseModel):
    metric: str
    data: list[dict] = []
