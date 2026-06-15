"""Analytics module — Pydantic schemas. PRD Section 8.8 + Sprint 9."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class AnalyticsInsightResponse(BaseModel):
    id: UUID
    snapshot_id: UUID
    insight_type: str
    title: str
    description: str
    impact_score: int
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsSnapshotResponse(BaseModel):
    id: UUID
    user_id: UUID
    total_applications: int
    total_interviews: int
    total_offers: int
    total_rejections: int
    total_acceptances: int
    response_rate: float
    interview_rate: float
    offer_rate: float
    acceptance_rate: float
    average_ats_score: float
    average_match_score: float
    strongest_resume_version_id: UUID | None
    generated_at: datetime

    # Deltas and Funnel counts
    ats_score_delta: float | None = None
    match_score_delta: float | None = None
    application_rate_delta: float | None = None
    interview_rate_delta: float | None = None
    funnel_stage_counts: dict[str, int] | None = None

    class Config:
        from_attributes = True


class ResumeIntelItem(BaseModel):
    id: UUID | None = None
    version_number: int | None = None
    original_filename: str | None = None
    score: float | None = None


class ResumeIntelligenceResponse(BaseModel):
    best_performing: ResumeIntelItem | None = None
    worst_performing: ResumeIntelItem | None = None
    highest_ats: ResumeIntelItem | None = None
    highest_match: ResumeIntelItem | None = None


class SkillGapCategoryItem(BaseModel):
    category: str
    count: int


class MissingSkillItem(BaseModel):
    skill: str
    count: int


class ImpactSkillItem(BaseModel):
    skill: str
    score: float


class BlockingSkillItem(BaseModel):
    skill: str
    count: int


class SkillIntelligenceResponse(BaseModel):
    top_missing_skills: list[MissingSkillItem] = []
    most_frequent_gap_categories: list[SkillGapCategoryItem] = []
    highest_impact_skills: list[ImpactSkillItem] = []
    skills_blocking_interviews: list[BlockingSkillItem] = []


class AnalyticsOverviewResponse(BaseModel):
    snapshot: AnalyticsSnapshotResponse
    resume_intelligence: ResumeIntelligenceResponse
    skill_intelligence: SkillIntelligenceResponse
    insights: list[AnalyticsInsightResponse] = []
