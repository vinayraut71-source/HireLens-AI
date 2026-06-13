"""
Roadmap module — models.
PRD Section 7.2: learning_roadmaps, roadmap_modules.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import BaseModel


class LearningRoadmap(BaseModel):
    """Logical personalized curriculum tailored to bridge a user's skill gaps. PRD Section 7.2."""

    __tablename__ = "learning_roadmaps"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    match_result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_results.id", ondelete="SET NULL"), nullable=True
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
        UUID(as_uuid=True), ForeignKey("learning_roadmaps.id", ondelete="CASCADE"), nullable=False
    )
    skill_gap_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_gaps.id", ondelete="SET NULL"), nullable=True
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
