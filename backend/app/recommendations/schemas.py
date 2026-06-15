"""Recommendations module — Pydantic schemas. PRD Section 8.9 + Sprint 10."""
from typing import Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class RecommendationSignalResponse(BaseModel):
    id: UUID
    user_id: UUID
    application_id: UUID | None = None
    resume_version_id: UUID | None = None
    job_match_id: UUID | None = None
    signal_type: str
    signal_source: Literal["application", "roadmap", "analytics", "resume", "job_match"]
    signal_value: float
    confidence_score: float
    signal_weight: float
    metadata: dict = Field(default_factory=dict, alias="metadata_")

    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class SignalGenerationSummary(BaseModel):
    generated_count: int
    skipped_count: int


class SkillSuccessItem(BaseModel):
    skill: str
    score: float


class SkillRejectionItem(BaseModel):
    skill: str
    score: float


class ResumePerfItem(BaseModel):
    id: UUID
    version_number: int
    filename: str
    interview_rate: float
    applications_sent: int


class JobCategoryItem(BaseModel):
    company: str | None = None
    title: str | None = None
    interview_rate: float
    applications_sent: int


class FeedbackSummaryResponse(BaseModel):
    skills_success: list[SkillSuccessItem] = []
    skills_rejection: list[SkillRejectionItem] = []
    best_performing_resumes: list[ResumePerfItem] = []
    highest_converting_categories: list[JobCategoryItem] = []
    signal_counts_by_type: dict[str, int] = {}


class JobRecommendationResponse(BaseModel):
    id: UUID
    job_id: UUID
    resume_version_id: UUID
    recommendation_score: float
    match_score: float
    ats_score: float
    skill_gap_score: float
    feedback_score: float
    confidence_score: float
    recommendation_reason: dict
    recommendation_status: str
    job_snapshot: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobDiscoveryResponse(BaseModel):
    recommendations: list[JobRecommendationResponse]
    total_recommendations: int
    generated_at: datetime


class RecommendationStatusUpdate(BaseModel):
    status: Literal["recommended", "viewed", "saved", "dismissed", "applied"]


