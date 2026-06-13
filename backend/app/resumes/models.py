"""
Resumes module — models.
PRD Section 7.2: resume_profiles, resume_versions, resume_version_embeddings,
ats_score_history, match_score_history.
"""
import uuid
from datetime import datetime

from sqlalchemy import (Boolean, DateTime, Float, ForeignKey, Integer,
                        LargeBinary, String, Text, UniqueConstraint, Index)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import BaseModel, SoftDeleteMixin


class ResumeProfile(SoftDeleteMixin, BaseModel):
    """Parent entity for a logical resume document. PRD Section 7.2."""
    __tablename__ = "resume_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    active_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_versions.id", ondelete="SET NULL", use_alter=True, name="fk_resume_profiles_active_version"),
        nullable=True,
    )
    version_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    versions: Mapped[list["ResumeVersion"]] = relationship(
        back_populates="profile", foreign_keys="ResumeVersion.profile_id", cascade="all, delete-orphan"
    )
    active_version: Mapped["ResumeVersion | None"] = relationship(
        foreign_keys=[active_version_id], post_update=True
    )


class ResumeVersion(SoftDeleteMixin, BaseModel):
    """Immutable snapshot — PRD Section 7.2, 13.2."""
    __tablename__ = "resume_versions"

    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_profiles.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    upload_source: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Structured parsing fields
    contact_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    education: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    experience: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    skills: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    certifications: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    
    # Legacy / future placeholder fields kept as nullable to prevent breaks
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ats_feedback: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ats_score_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="processing", server_default="processing")

    profile: Mapped["ResumeProfile"] = relationship(back_populates="versions", foreign_keys=[profile_id])

    __table_args__ = (
        UniqueConstraint("profile_id", "version_number", name="uq_resume_versions_profile_version"),
        Index("ix_resume_versions_skills", "skills", postgresql_using="gin"),
        Index("ix_resume_versions_contact_info", "contact_info", postgresql_using="gin"),
    )


class ResumeVersionEmbedding(BaseModel):
    __tablename__ = "resume_version_embeddings"

    version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), unique=True, nullable=False)
    embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)


class AtsScoreHistory(BaseModel):
    __tablename__ = "ats_score_history"

    version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_profiles.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    score_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scored_by: Mapped[str] = mapped_column(String(20), default="system", server_default="system")


class MatchScoreHistory(BaseModel):
    __tablename__ = "match_score_history"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_profiles.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    matched_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    missing_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    match_result_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("match_results.id", ondelete="SET NULL"), nullable=True)
