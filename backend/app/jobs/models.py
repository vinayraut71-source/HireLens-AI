"""Jobs module — models. PRD Section 7.2: jobs, job_embeddings, match_results, skill_gaps, job_matches."""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.shared.base import BaseModel, SoftDeleteMixin

class Job(SoftDeleteMixin, BaseModel):
    __tablename__ = "jobs"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    discovered_by_agent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

class JobEmbedding(BaseModel):
    __tablename__ = "job_embeddings"
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

class MatchResult(BaseModel):
    __tablename__ = "match_results"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    matched_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    partial_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    missing_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    ai_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)

class SkillGap(BaseModel):
    __tablename__ = "skill_gaps"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    match_result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("match_results.id", ondelete="CASCADE"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="identified", server_default="identified")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class JobMatch(BaseModel):
    """Sprint 5: Intelligent Job Matching result. Deterministic scoring of a resume against a saved job."""
    __tablename__ = "job_matches"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Composite scores (0-100)
    overall_match_score: Mapped[float] = mapped_column(Float, nullable=False)
    skills_match_score: Mapped[float] = mapped_column(Float, nullable=False)
    experience_match_score: Mapped[float] = mapped_column(Float, nullable=False)
    education_match_score: Mapped[float] = mapped_column(Float, nullable=False)
    keyword_match_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Breakdown data
    matched_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    missing_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    strengths: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    weaknesses: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    fit_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    improvement_actions: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")

    # Relationships
    job: Mapped["Job"] = relationship(foreign_keys=[job_id])

    __table_args__ = (
        Index("ix_job_matches_user_job_version", "user_id", "job_id", "resume_version_id"),
    )
