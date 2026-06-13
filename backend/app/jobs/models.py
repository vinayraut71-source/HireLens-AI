"""Jobs module — models. PRD Section 7.2: jobs, job_embeddings, match_results, skill_gaps."""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.base import BaseModel

class Job(BaseModel):
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
