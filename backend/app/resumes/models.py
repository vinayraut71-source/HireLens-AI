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

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    active_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_versions.id", ondelete="SET NULL", use_alter=True, name="fk_resume_profiles_active_version"),
        nullable=True,
        index=True,
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
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
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

    version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    score_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scored_by: Mapped[str] = mapped_column(String(20), default="system", server_default="system")


class MatchScoreHistory(BaseModel):
    __tablename__ = "match_score_history"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    matched_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    missing_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    match_result_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("match_results.id", ondelete="SET NULL"), nullable=True, index=True)


class ATSAnalysis(BaseModel):
    """ATS Analysis results for a resume version against a job description. PRD Section 7.2."""
    __tablename__ = "ats_analyses"

    resume_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_description_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ats_score: Mapped[int] = mapped_column(Integer, nullable=False)
    keyword_score: Mapped[int] = mapped_column(Integer, nullable=False)
    skills_score: Mapped[int] = mapped_column(Integer, nullable=False)
    experience_score: Mapped[int] = mapped_column(Integer, nullable=False)
    education_score: Mapped[int] = mapped_column(Integer, nullable=False)
    missing_keywords: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    matched_keywords: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    recommendations: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")

    # Enhanced design fields
    matched_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    missing_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    resume_strengths: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    resume_weaknesses: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    matched_sections: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")

    resume_version: Mapped["ResumeVersion"] = relationship(foreign_keys=[resume_version_id])


class ResumeTailoringSession(BaseModel):
    __tablename__ = "resume_tailoring_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ats_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ats_analyses.id", ondelete="SET NULL"), nullable=True
    )
    job_match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_matches.id", ondelete="SET NULL"), nullable=True
    )
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_description_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    original_ats_score: Mapped[int] = mapped_column(Integer, nullable=False)
    tailored_ats_score: Mapped[int] = mapped_column(Integer, nullable=False)
    tailoring_mode: Mapped[str] = mapped_column(String(20), nullable=False)  # deterministic, ai_assisted
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # pending, completed, failed

    tailoring_quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resume_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    suggestions: Mapped[list["TailoredResumeSuggestion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "resume_version_id",
            "job_description_hash",
            "tailoring_mode",
            name="uq_resume_tailoring_sessions_version_hash_mode"
        ),
    )



class TailoredResumeSuggestion(BaseModel):
    __tablename__ = "tailored_resume_suggestions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_tailoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_name: Mapped[str] = mapped_column(String(30), nullable=False)  # summary, experience, education, skills, projects, certifications
    suggestion_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # keyword_addition, bullet_rewrite, section_improvement, skill_recommendation, ats_optimization
    original_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    severity_level: Mapped[str | None] = mapped_column(String(20), nullable=True)  # low, medium, high, critical


    session: Mapped["ResumeTailoringSession"] = relationship(back_populates="suggestions")


