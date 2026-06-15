"""
Roadmap module — models.
PRD Section 7.2: learning_roadmaps, roadmap_modules.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import BaseModel


class LearningRoadmap(BaseModel):
    """Logical personalized curriculum tailored to bridge a user's skill gaps. PRD Section 7.2."""

    __tablename__ = "learning_roadmaps"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    match_result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_results.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    estimated_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)

    modules: Mapped[list["RoadmapModule"]] = relationship(
        back_populates="roadmap", cascade="all, delete-orphan"
    )


class RoadmapModule(BaseModel):
    """Step-by-step module in a roadmap. PRD Section 7.2."""

    __tablename__ = "roadmap_modules"

    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_roadmaps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_gap_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_gaps.id", ondelete="SET NULL"), nullable=True, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resources: Mapped[dict] = mapped_column(JSONB, default=list, server_default="[]")
    project_idea: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    roadmap: Mapped["LearningRoadmap"] = relationship(back_populates="modules")


class CareerRoadmap(BaseModel):
    """Sprint 7: Career Roadmap model representing learning progress for a JobMatch."""
    __tablename__ = "career_roadmaps"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    total_estimated_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    roadmap_status: Mapped[str] = mapped_column(
        String(20), default="active", server_default="active", nullable=False
    )

    milestones: Mapped[list["RoadmapMilestone"]] = relationship(
        back_populates="roadmap", cascade="all, delete-orphan", order_by="RoadmapMilestone.milestone_order"
    )


class RoadmapMilestone(BaseModel):
    """Sprint 7: Roadmap milestone representing a single skill gap in the learning sequence."""
    __tablename__ = "roadmap_milestones"

    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_roadmaps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_gap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_gap_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    milestone_order: Mapped[int] = mapped_column(Integer, nullable=False)
    milestone_title: Mapped[str] = mapped_column(String(255), nullable=False)
    estimated_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending", nullable=False
    )

    roadmap: Mapped["CareerRoadmap"] = relationship(back_populates="milestones")
