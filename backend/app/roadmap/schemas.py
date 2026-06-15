"""Roadmap module — schemas. PRD Section 8.6."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class RoadmapModuleResponse(BaseModel):
    id: UUID
    order_index: int
    title: str
    description: str | None = None
    estimated_hours: int | None = None
    resources: list = []
    project_idea: str | None = None
    status: str
    completed_at: datetime | None = None
    class Config: from_attributes = True

class RoadmapResponse(BaseModel):
    id: UUID
    title: str
    target_role: str | None = None
    status: str
    estimated_hours: int | None = None
    modules: list[RoadmapModuleResponse] = []
    class Config: from_attributes = True

class RoadmapCreateRequest(BaseModel):
    match_result_id: UUID
    title: str | None = None


# --- Career Roadmap Generator Schemas (Sprint 7) ---

class MilestoneResponse(BaseModel):
    id: UUID
    roadmap_id: UUID
    skill_gap_id: UUID
    milestone_order: int
    milestone_title: str
    estimated_weeks: int
    priority_score: int
    completion_status: str

    class Config:
        from_attributes = True


class CareerRoadmapResponse(BaseModel):
    id: UUID
    user_id: UUID
    resume_version_id: UUID
    job_match_id: UUID
    generated_at: datetime
    total_estimated_weeks: int
    roadmap_status: str
    milestones: list[MilestoneResponse]

    class Config:
        from_attributes = True


class MilestonePatchRequest(BaseModel):
    completion_status: str
