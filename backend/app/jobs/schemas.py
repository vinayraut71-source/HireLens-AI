"""Jobs module — schemas. PRD Section 8.5: Job CRUD + Sprint 5 Job Matching."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# --- Job CRUD Schemas ---

class JobCreateRequest(BaseModel):
    title: str = Field(..., max_length=255)
    description: str = Field(..., max_length=50000)
    company: str | None = None
    source_url: str | None = None
    location: str | None = None
    remote_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None


class JobResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    company: str | None
    description: str
    source_url: str | None
    location: str | None
    remote_type: str | None
    salary_min: int | None
    salary_max: int | None
    required_skills: list
    is_saved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class JobUpdateRequest(BaseModel):
    title: str | None = None
    company: str | None = None
    description: str | None = None
    is_saved: bool | None = None


# --- Job Match Schemas (Sprint 5) ---

class JobMatchRequest(BaseModel):
    """Request body for POST /api/v1/jobs/{job_id}/match."""
    resume_version_id: UUID


class JobMatchResponse(BaseModel):
    """Response body for job match results."""
    id: UUID
    user_id: UUID
    resume_version_id: UUID
    job_id: UUID
    overall_match_score: float
    skills_match_score: float
    experience_match_score: float
    education_match_score: float
    keyword_match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    weaknesses: list[str]
    fit_summary: str
    improvement_actions: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class JobMatchListResponse(BaseModel):
    """List item for GET /api/v1/jobs/matches."""
    id: UUID
    job_id: UUID
    resume_version_id: UUID
    overall_match_score: float
    skills_match_score: float
    experience_match_score: float
    education_match_score: float
    keyword_match_score: float
    fit_summary: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Legacy Schemas (kept for compatibility) ---

class MatchRequest(BaseModel):
    version_id: UUID


class MatchResponse(BaseModel):
    match_result_id: UUID
    overall_score: float
    ats_score: int | None = None
    matched_skills: list = []
    partial_skills: list = []
    missing_skills: list = []
    ai_analysis: str | None = None


class SkillGapResponse(BaseModel):
    id: UUID
    skill_name: str
    priority: str
    category: str | None = None
    status: str

    class Config:
        from_attributes = True
